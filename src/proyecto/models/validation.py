"""Validación final e interpretación (etapa 7): abrir la prueba UNA sola vez y explicar qué hace el modelo.

Piezas (todas se prueban en `tests/test_validation.py`):
  * `decide_calibration`: regla escrita antes de mirar para decidir si se calibran las probabilidades;
  * `freeze_decisions` y `open_test_once`: dejan constancia de qué se decidió y cuándo se abrió la prueba, y
    evitan que se vuelva a evaluar el modelo con ella;
  * `metric_with_ci`: una métrica de negocio con su intervalo del 95 %, remuestreando estudiantes (filas);
  * `segment_table` y `age_band`: el desempeño por grupo (equidad) y la carga de trabajo;
  * `coefficient_table` y `shap_importance`: por qué decide así el modelo.

Cada fila es un estudiante distinto (`student_id` único), por eso se remuestrean filas y no grupos.
"""
import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from proyecto.models.train import business_metrics
from proyecto.models.tuning import bootstrap_metric_ci

# Regla de calibración (escrita ANTES de mirar): se calibra solo si el log loss mejora al menos esto Y el costo no
# empeora de forma distinguible (el límite inferior del intervalo de «calibrado − sin calibrar» no es positivo).
MIN_LOG_LOSS_GAIN = 0.005

AGE_BINS = (0, 15, 17, 120)
AGE_LABELS = ("≤15", "16–17", "≥18")


def decide_calibration(log_loss_plain: float, log_loss_calibrated: float, cost_diff_low: float,
                       min_gain: float = MIN_LOG_LOSS_GAIN) -> bool:
    """True si conviene calibrar: el log loss baja más de `min_gain` y el costo no empeora de forma distinguible.

    `cost_diff_low` es el límite inferior del intervalo del 95 % de (costo calibrado − costo sin calibrar):
    si es positivo, calibrar empeora el costo con confianza y no se calibra.
    """
    return bool(log_loss_calibrated < log_loss_plain - min_gain and not cost_diff_low > 0)


def freeze_decisions(decisions: dict, path: str | Path, test_opened: bool) -> dict:
    """Guarda las decisiones con fecha y hora, ANTES de abrir la prueba. Si la prueba ya se abrió, no se reescriben.

    Devuelve las decisiones vigentes (las nuevas, o las ya guardadas si la prueba ya estaba abierta).
    """
    path = Path(path)
    if test_opened and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    frozen = {"fecha_y_hora": datetime.now().isoformat(timespec="seconds"), **decisions}
    path.write_text(json.dumps(frozen, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    return frozen


def open_test_once(marker: str | Path, cache: str | Path, predict_fn, note: str = "") -> tuple[object, bool]:
    """Evalúa con la prueba UNA sola vez. Devuelve (resultado, ¿se abrió ahora?).

    * Primera vez: llama a `predict_fn()`, guarda su resultado en `cache` y escribe `marker` con la fecha y hora.
    * Después: reutiliza lo guardado en `cache` y NO vuelve a llamar a `predict_fn` (la prueba no se vuelve a mirar).
    * Si hay marca pero falta el `cache`, falla: reabrir la prueba hay que declararlo en el reporte.
    """
    marker, cache = Path(marker), Path(cache)
    if marker.exists() and cache.exists():
        return joblib.load(cache), False
    if marker.exists():
        raise RuntimeError("La prueba ya se abrió y no hay resultados guardados: declararlo en el reporte antes de reabrirla.")
    result = predict_fn()
    joblib.dump(result, cache)
    marker.write_text(f"Prueba abierta el {datetime.now().isoformat(timespec='seconds')}. {note} Una sola vez.\n", encoding="utf-8")
    return result, True


def metric_with_ci(y_fail, p_fail, threshold: float, key: str, n_boot: int = 1000, seed: int = 42):
    """Una métrica de `business_metrics` (p. ej. `cost`, `recall_fail`, `npv`) con su intervalo del 95 %.

    Remuestrea estudiantes (filas). Devuelve (valor, límite inferior, límite superior).
    """
    def fn(y, p):
        return business_metrics(y, p >= threshold)[key]

    return bootstrap_metric_ci(y_fail, p_fail, fn, n_boot=n_boot, seed=seed)


def age_band(age: pd.Series) -> pd.Series:
    """Tramos de edad para la auditoría. El dataset incluye menores de edad: se ven por separado."""
    return pd.cut(age, bins=AGE_BINS, labels=AGE_LABELS).astype(str)


def segment_table(y_fail, p_fail, threshold: float, groups: pd.DataFrame, columns) -> pd.DataFrame:
    """Desempeño por grupo: casos, % real de `Fail`, % de alertas, *recall*, precisión, NPV y costo.

    `groups` debe tener el mismo orden que `y_fail`/`p_fail`. Un valor que no se puede calcular (p. ej. NPV de un
    grupo sin nadie tranquilizado) queda como NaN, no como 0.
    """
    y_fail = np.asarray(y_fail).astype(int)
    alert = np.asarray(p_fail) >= threshold
    if len(groups) != len(y_fail):
        raise ValueError("`groups` y `y_fail` deben tener la misma longitud.")
    rows = []
    for column in columns:
        values = groups[column].astype(str).to_numpy()
        for value in sorted(set(values)):
            mask = values == value
            m = business_metrics(y_fail[mask], alert[mask])
            rows.append({
                "variable": column, "grupo": value, "casos": int(mask.sum()),
                "% Fail real": 100 * y_fail[mask].mean(), "% alertas": m["alerts_per_100"],
                "recall Fail": m["recall_fail"], "precisión Fail": m["precision_fail"], "NPV": m["npv"], "costo": m["cost"],
            })
    return pd.DataFrame(rows).set_index(["variable", "grupo"])


def coefficient_table(pipeline) -> pd.DataFrame:
    """Coeficientes de la regresión logística del pipeline, con el nombre de cada variable transformada.

    Las numéricas van estandarizadas (`scale=True`), así que sus coeficientes son comparables entre sí. Un coeficiente
    positivo empuja hacia `Fail`. Las categóricas son 0/1, no estandarizadas.
    """
    names = [n.split("__", 1)[-1] for n in pipeline.named_steps["prep"].get_feature_names_out()]
    coef = np.ravel(pipeline.named_steps["model"].coef_)
    if len(names) != len(coef):
        raise ValueError("El número de coeficientes no coincide con el de variables transformadas.")
    table = pd.DataFrame({"coeficiente": coef, "odds ratio": np.exp(coef)}, index=names)
    return table.reindex(table["coeficiente"].abs().sort_values(ascending=False).index)


def shap_importance(pipeline, X_sample: pd.DataFrame) -> pd.DataFrame:
    """Importancia SHAP (|SHAP| medio hacia `Fail`) de un pipeline lineal, calculada sobre una muestra del ENTRENAMIENTO.

    Explica al modelo, no al mundo; y las variables correlacionadas se reparten el crédito.
    """
    import shap

    prep, model = pipeline.named_steps["prep"], pipeline.named_steps["model"]
    Xt = prep.transform(X_sample)
    names = [n.split("__", 1)[-1] for n in prep.get_feature_names_out()]
    values = shap.LinearExplainer(model, Xt).shap_values(Xt)
    values = values[1] if isinstance(values, list) else values
    table = pd.DataFrame({"|SHAP| medio": np.abs(values).mean(axis=0)}, index=names)
    return table.sort_values("|SHAP| medio", ascending=False)


def student_contributions(pipeline, X_row: pd.DataFrame, top: int = 6) -> pd.DataFrame:
    """Qué empuja la predicción de UN estudiante hacia `Fail` (+) o hacia `Pass` (−), en la escala del logit.

    En una regresión logística la contribución de cada variable es `coeficiente × valor transformado`; el resto es el
    intercepto. Devuelve las `top` contribuciones más grandes en valor absoluto.
    """
    if len(X_row) != 1:
        raise ValueError("Pasa exactamente un estudiante.")
    prep, model = pipeline.named_steps["prep"], pipeline.named_steps["model"]
    names = [n.split("__", 1)[-1] for n in prep.get_feature_names_out()]
    transformed = np.ravel(prep.transform(X_row))
    contribution = np.ravel(model.coef_) * transformed
    table = pd.DataFrame({"valor transformado": transformed, "contribución al logit": contribution}, index=names)
    return table.reindex(table["contribución al logit"].abs().sort_values(ascending=False).index).head(top)
