"""Candidatos, pipeline y métricas de negocio para medir variables (etapa 4) y comparar modelos (etapa 5).

Las definiciones son las del caso de negocio (`notebooks/01b_caso_negocio_aprueba_o_no.ipynb`):
  * clase de interés = `Fail` (el estudiante pierde el curso: nota < 70);
  * «alerta» = el modelo avisa que el estudiante está en riesgo;
  * costos (SUPUESTO, la institución debe validarlos): falso negativo = 5, falso positivo = 1.

Con esos costos, la decisión que minimiza el costo esperado es avisar cuando P(Fail) >= 1 / (1 + 5) = 0,167
(`decide_alert`). El modelo supera a «avisar a todos» solo si su NPV es mayor que 5 / 6 = 83,3 %.
"""
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from xgboost import XGBClassifier

from proyecto.data.cleaning import TARGET
from proyecto.features.engineering import add_features, build_preprocessor

FALSE_POSITIVE_COST = 1     # avisar a quien habría aprobado (supuesto)
FALSE_NEGATIVE_COST = 5     # NO avisar a quien pierde el curso (supuesto)
RANDOM_STATE = 42
TOP_K_PERCENTS = (30, 50)   # «si solo se puede avisar al k % más riesgoso»: capacidad de tutoría (a definir por la institución)


def encode_target(y: pd.Series) -> np.ndarray:
    """`Fail` -> 1 (clase de interés), `Pass` -> 0. Falla si aparece cualquier otro valor."""
    values = set(y.unique())
    if not values <= {"Pass", "Fail"}:
        raise ValueError(f"El objetivo solo puede ser 'Pass' o 'Fail'; encontré {sorted(map(str, values))}")
    return (y == "Fail").to_numpy().astype(int)


def decision_threshold(fn_cost: float = FALSE_NEGATIVE_COST, fp_cost: float = FALSE_POSITIVE_COST) -> float:
    """P(Fail) desde la cual conviene avisar: costo del falso positivo / (costo FP + costo FN)."""
    return fp_cost / (fp_cost + fn_cost)


def decide_alert(p_fail, fn_cost: float = FALSE_NEGATIVE_COST, fp_cost: float = FALSE_POSITIVE_COST) -> np.ndarray:
    """True = avisar. Con probabilidades bien calibradas es la decisión de menor costo esperado."""
    return np.asarray(p_fail) >= decision_threshold(fn_cost, fp_cost)


def business_metrics(
    y_fail, alert, fn_cost: float = FALSE_NEGATIVE_COST, fp_cost: float = FALSE_POSITIVE_COST
) -> dict:
    """Métricas de negocio a partir de quién pierde el curso (`y_fail`, 0/1) y a quién se avisó (`alert`).

    Si una razón no se puede calcular (p. ej. NPV cuando el modelo no tranquiliza a nadie) devuelve NaN en vez de
    inventar 0: un 0 se confundiría con «malísimo».
    """
    y_fail = np.asarray(y_fail).astype(bool)
    alert = np.asarray(alert).astype(bool)
    tp = int((y_fail & alert).sum())      # perdía el curso y se avisó
    fn = int((y_fail & ~alert).sum())     # perdía el curso y NO se avisó (error caro)
    fp = int((~y_fail & alert).sum())     # habría aprobado y se avisó (error barato)
    tn = int((~y_fail & ~alert).sum())    # habría aprobado y no se avisó
    total = len(y_fail)

    def ratio(a: int, b: int) -> float:
        return a / b if b else float("nan")

    recall, precision = ratio(tp, tp + fn), ratio(tp, tp + fp)
    specificity = ratio(tn, tn + fp)
    f1 = ratio(2 * tp, 2 * tp + fp + fn)                 # = 2PR / (P + R)
    f2 = ratio(5 * tp, 5 * tp + 4 * fn + fp)             # = 5PR / (4P + R): pesa más el recall
    return {
        "cost": (fn_cost * fn + fp_cost * fp) / total,
        "recall_fail": recall,
        "precision_fail": precision,
        "npv": ratio(tn, tn + fn),
        "specificity": specificity,
        "f1_fail": f1,
        "f2_fail": f2,
        "balanced_accuracy": (recall + specificity) / 2,
        "accuracy": (tp + tn) / total,
        "alerts_per_100": 100 * (tp + fp) / total,
        "tp": tp, "fn": fn, "fp": fp, "tn": tn,
    }


def top_k_alert(p_fail, k_percent: float) -> np.ndarray:
    """True para el `k_percent` % de estudiantes con mayor P(Fail): avisar solo hasta donde alcanza la capacidad."""
    p_fail = np.asarray(p_fail, dtype=float)
    n_alert = int(len(p_fail) * k_percent / 100)
    alert = np.zeros(len(p_fail), dtype=bool)
    alert[np.argsort(-p_fail, kind="stable")[:n_alert]] = True
    return alert


def candidates(random_state: int = RANDOM_STATE) -> dict:
    """Modelos del torneo: nombre -> (modelo, ¿necesita variables escaladas?).

    La línea base (`DummyClassifier(prior)`) siempre predice la tasa de `Fail` (69,2 %): con el umbral de 0,167
    equivale a «avisar a todos», la estrategia sin modelo a vencer.
    """
    return {
        "línea base (avisar a todos)": (DummyClassifier(strategy="prior"), False),
        "regresión logística": (LogisticRegression(max_iter=1000, random_state=random_state), True),
        "random forest": (
            RandomForestClassifier(n_estimators=200, min_samples_leaf=5, n_jobs=4, random_state=random_state), False),
        "lightgbm": (
            LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=random_state,
                           verbose=-1, n_jobs=4), False),
        "xgboost": (
            XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=6, tree_method="hist",
                          random_state=random_state, n_jobs=4, eval_metric="logloss"), False),
    }


def metrics_from_proba(y_fail, p_fail) -> dict:
    """Todas las métricas de un conjunto de predicciones: la decisión de negocio y las que usan solo las probabilidades."""
    y_fail = np.asarray(y_fail).astype(int)
    p_fail = np.asarray(p_fail, dtype=float)
    out = business_metrics(y_fail, decide_alert(p_fail))
    out["cost_argmax"] = business_metrics(y_fail, p_fail >= 0.5)["cost"]     # con la «clase más probable», sin costos
    for k in TOP_K_PERCENTS:                                                 # si solo se puede avisar al k % más riesgoso
        m_k = business_metrics(y_fail, top_k_alert(p_fail, k))
        out[f"precision_top{k}"], out[f"recall_top{k}"], out[f"cost_top{k}"] = m_k["precision_fail"], m_k["recall_fail"], m_k["cost"]
    out["pr_auc_fail"] = average_precision_score(y_fail, p_fail)
    out["roc_auc"] = roc_auc_score(y_fail, p_fail)
    out["log_loss"] = log_loss(y_fail, np.clip(p_fail, 1e-15, 1 - 1e-15), labels=[0, 1])
    return out


def build_pipeline(
    model,
    drop=(),
    engineered=(),
    add_missing_indicator: bool = True,
    scale: bool = False,
) -> Pipeline:
    """Pipeline completo: (variables nuevas) -> imputación y codificación -> modelo. Se guarda entero.

    Todo lo que aprende de los datos (medianas, categorías) se ajusta solo con el entrenamiento de cada pliegue.
    """
    engineered = tuple(engineered)
    steps = []
    if engineered:
        steps.append(("features", FunctionTransformer(add_features, kw_args={"engineered": engineered})))
    steps.append(("prep", build_preprocessor(drop, engineered, add_missing_indicator, scale)))
    steps.append(("model", model))
    return Pipeline(steps)


def evaluate_folds(pipeline, X: pd.DataFrame, y_fail, folds) -> pd.DataFrame:
    """Valida con los pliegues dados. Una fila por pliegue con todas las métricas y el tiempo de ajuste.

    `folds` es la lista de (índices de entrenamiento, índices de validación) de `make_folds`: los mismos para todas
    las variantes que se comparen. La prueba (`test.joblib`) no interviene.
    """
    if TARGET in X.columns:
        raise ValueError(f"X no debe incluir el objetivo '{TARGET}'.")
    y_fail = np.asarray(y_fail)
    rows = []
    for fold, (train_idx, valid_idx) in enumerate(folds):
        model = clone(pipeline)
        start = time.time()
        model.fit(X.iloc[train_idx], y_fail[train_idx])
        seconds = time.time() - start
        p_fail = model.predict_proba(X.iloc[valid_idx])[:, 1]
        rows.append({"fold": fold, **metrics_from_proba(y_fail[valid_idx], p_fail), "fit_seconds": seconds})
    return pd.DataFrame(rows).set_index("fold")
