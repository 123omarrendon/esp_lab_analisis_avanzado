"""Optimización de hiperparámetros con Optuna, registrando cada ensayo en MLflow (etapa 6).

Qué se optimiza: el modelo ganador del torneo (`reports/05_torneo.md`), la **regresión logística**. Casi no tiene
hiperparámetros, así que el espacio de búsqueda es corto y está acotado por lo que se sabe del algoritmo:

  * `C`: inversa de la regularización (más chico = coeficientes más contenidos). Escala logarítmica.
  * `threshold`: P(Fail) desde la cual se avisa. NO es un parámetro del modelo sino de la **decisión**: la etapa 5
    lo fijó en 1 / (1 + 5) = 0,167 suponiendo probabilidades calibradas; aquí se ajusta con validación.

La mejor puntuación de una búsqueda es **optimista** (se escoge el máximo de muchas pruebas). Por eso el notebook
`06b_optimizacion_aprueba_o_no.ipynb` reserva estudiantes que la búsqueda nunca ve y compara ahí, con intervalo del 95 %
(`bootstrap_cost_difference`), el modelo con parámetros de partida y con los optimizados. Cada estudiante es una fila
independiente (`student_id` único), así que el intervalo remuestrea **filas**; si hubiera estudiantes repetidos habría
que remuestrear por grupo.
"""
from pathlib import Path

import mlflow
import numpy as np
import optuna
import pandas as pd
from sklearn.linear_model import LogisticRegression

from proyecto.models.train import (FALSE_NEGATIVE_COST, FALSE_POSITIVE_COST, RANDOM_STATE, build_pipeline,
                                   decision_threshold, evaluate_folds)
from proyecto.tracking.mlflow_utils import log_run

# Rangos de la búsqueda (documentados: el notebook los muestra en una tabla).
C_RANGE = (1e-3, 1e2)
THRESHOLD_RANGE = (0.05, 0.40)     # alrededor del umbral teórico de 0,167


def lr_space(trial: optuna.Trial, tune_threshold: bool = True) -> dict:
    """Espacio de búsqueda de la regresión logística; los rangos salen del conocimiento del algoritmo, no del azar."""
    params = {"C": trial.suggest_float("C", *C_RANGE, log=True)}
    if tune_threshold:
        params["threshold"] = trial.suggest_float("threshold", *THRESHOLD_RANGE)
    return params


def make_lr(params: dict, random_state: int = RANDOM_STATE) -> LogisticRegression:
    """Regresión logística con los parámetros del ensayo. `threshold` no es del modelo y se ignora aquí."""
    model_params = {k: v for k, v in params.items() if k != "threshold"}
    return LogisticRegression(max_iter=1000, random_state=random_state, **model_params)


# nombre -> (función del espacio, fábrica del modelo, ¿necesita variables escaladas?)
MODELS = {
    "regresión logística": (lr_space, make_lr, True),
}

# Métricas que se pueden optimizar y en qué dirección. Todas salen de `metrics_from_proba`.
OBJETIVOS = {
    "cost": "minimize",             # negocio: costo esperado por estudiante (5 : 1)
    "log_loss": "minimize",         # calidad de las probabilidades
    "roc_auc": "maximize",          # técnica: capacidad de ordenar
    "pr_auc_fail": "maximize",      # técnica: precisión-recall de la clase de interés
    "f1_fail": "maximize",
    "balanced_accuracy": "maximize",
    "accuracy": "maximize",
    "recall_fail": "maximize",      # cuidado: solo, empuja a avisar a todos; vigílalo junto a la precisión y el NPV
}
# No dependen del umbral: ajustarlo no cambia su valor, así que no se busca.
THRESHOLD_FREE = {"log_loss", "roc_auc", "pr_auc_fail"}


def tune(name: str, X: pd.DataFrame, y: np.ndarray, folds, n_trials: int, seed: int = RANDOM_STATE, log: bool = True,
         storage: str | None = None, metric: str = "cost"):
    """Corre un estudio de Optuna que optimiza `metric` (ver OBJETIVOS). Cada ensayo queda como ejecución anidada en MLflow.

    En MLflow se registran TODAS las métricas de cada ensayo (negocio y técnicas, con su desviación entre pliegues),
    aunque solo una se optimice: así se puede ordenar y comparar la lista por cualquiera de ellas.

    Con `storage` (ruta de un archivo .db) el estudio se guarda en disco y **se reanuda**: si la ejecución se corta,
    al volver a llamar solo se hacen los ensayos que faltan hasta completar `n_trials`.
    """
    if metric not in OBJETIVOS:
        raise ValueError(f"Métrica no soportada: {metric}. Opciones: {sorted(OBJETIVOS)}")
    if name not in MODELS:
        raise ValueError(f"Modelo no soportado: {name}. Opciones: {sorted(MODELS)}")
    space_fn, make_fn, scale = MODELS[name]
    tune_threshold = metric not in THRESHOLD_FREE

    def objective(trial: optuna.Trial) -> float:
        params = space_fn(trial, tune_threshold)
        results = evaluate_folds(build_pipeline(make_fn(params), scale=scale), X, y, folds, threshold=params.get("threshold"))
        trial.set_user_attr("cost_std", float(results["cost"].std()))
        trial.set_user_attr("log_loss", float(results["log_loss"].mean()))
        if log:
            board = {col: float(results[col].mean()) for col in results.columns}           # tablero completo (medias)
            board.update({f"{col}_std": float(results[col].std()) for col in results.columns if col != "fit_seconds"})
            log_run(
                f"{name}-trial-{trial.number}",
                params,
                board,
                tags={"etapa": "06_optimizacion", "modelo": name, "metrica_optimizada": metric},
                nested=True,
            )
        return float(results[metric].mean())

    study = optuna.create_study(
        direction=OBJETIVOS[metric], sampler=optuna.samplers.TPESampler(seed=seed),
        study_name=f"proyecto-{name}-{metric}", storage=(f"sqlite:///{Path(storage).as_posix()}" if storage else None),
        load_if_exists=True,
    )
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    done = len([t for t in study.trials if t.state.is_finished()])
    remaining = max(n_trials - done, 0)
    if done:
        print(f"  {name}: se reanuda el estudio ({done} ensayos ya hechos, faltan {remaining})")
    if log:
        with mlflow.start_run(run_name=f"optuna-{name}") as parent:
            study.optimize(objective, n_trials=remaining)
            mlflow.log_metric(f"best_{metric}", study.best_value)
            mlflow.log_params({f"best_{k}": v for k, v in study.best_params.items()})
            mlflow.set_tags({"etapa": "06_optimizacion", "modelo": name, "metrica_optimizada": metric})
            study.set_user_attr("mlflow_parent_run_id", parent.info.run_id)
        study.set_user_attr("metric", metric)
    else:
        study.optimize(objective, n_trials=remaining)
    return study


def row_costs(y_fail, alert, fn_cost: float = FALSE_NEGATIVE_COST, fp_cost: float = FALSE_POSITIVE_COST) -> np.ndarray:
    """Costo de cada estudiante: `fn_cost` si pierde el curso y no se avisó, `fp_cost` si se avisó y habría aprobado."""
    y_fail = np.asarray(y_fail).astype(bool)
    alert = np.asarray(alert).astype(bool)
    return fn_cost * (y_fail & ~alert) + fp_cost * (~y_fail & alert)


def bootstrap_cost_difference(y_true, proba_a, proba_b, threshold_a: float | None = None, threshold_b: float | None = None,
                              n_boot: int = 1000, seed: int = RANDOM_STATE):
    """Diferencia de costo (A menos B) con intervalo del 95 %, remuestreando ESTUDIANTES (filas).

    Cada estudiante es una fila independiente (`student_id` único). Un valor negativo significa que A cuesta menos que B.
    Devuelve (diferencia, límite inferior, límite superior). El umbral de cada modelo es el suyo (por defecto, 1 / 6).
    """
    y_true = np.asarray(y_true)
    thr_a = decision_threshold() if threshold_a is None else threshold_a
    thr_b = decision_threshold() if threshold_b is None else threshold_b
    diff = row_costs(y_true, np.asarray(proba_a) >= thr_a) - row_costs(y_true, np.asarray(proba_b) >= thr_b)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diff), size=(n_boot, len(diff)))
    boot = diff[idx].mean(axis=1)
    return float(diff.mean()), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def bootstrap_metric_ci(y_true, proba, metric_fn, n_boot: int = 300, seed: int = RANDOM_STATE):
    """Una métrica con su intervalo del 95 %, remuestreando ESTUDIANTES (filas).

    `metric_fn(y_true, proba)` devuelve un número. Devuelve (valor, límite inferior, límite superior).
    """
    y_true = np.asarray(y_true)
    proba = np.asarray(proba)
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(n_boot):
        rows = rng.integers(0, len(y_true), len(y_true))
        values.append(metric_fn(y_true[rows], proba[rows]))
    return float(metric_fn(y_true, proba)), float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))
