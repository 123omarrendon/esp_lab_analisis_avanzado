"""Pruebas de las métricas de negocio y del pipeline base (`src/proyecto/models/train.py`).

Caso de mano: 10 estudiantes, 3 pierden el curso. El modelo avisa a 2 de ellos y a 1 que habría aprobado:
  VP = 2, FN = 1, FP = 1, VN = 6  ->  costo = (5·1 + 1·1) / 10 = 0,6
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression

from proyecto.data.split import make_folds
from proyecto.models.train import (
    build_pipeline, business_metrics, candidates, decide_alert, decision_threshold, encode_target, evaluate_folds,
    metrics_from_proba, top_k_alert,
)
from toy import make_students

Y = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
ALERT = np.array([1, 1, 0, 1, 0, 0, 0, 0, 0, 0])


def test_business_metrics_by_hand():
    m = business_metrics(Y, ALERT)
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (2, 1, 1, 6)
    assert m["cost"] == pytest.approx(0.6)
    assert m["recall_fail"] == pytest.approx(2 / 3)
    assert m["precision_fail"] == pytest.approx(2 / 3)
    assert m["npv"] == pytest.approx(6 / 7)
    assert m["specificity"] == pytest.approx(6 / 7)
    assert m["alerts_per_100"] == pytest.approx(30)
    assert m["accuracy"] == pytest.approx(0.8)
    assert m["balanced_accuracy"] == pytest.approx((2 / 3 + 6 / 7) / 2)
    assert m["f1_fail"] == pytest.approx(2 / 3)
    assert m["f2_fail"] == pytest.approx(5 * (2 / 3) * (2 / 3) / (4 * (2 / 3) + 2 / 3))


def test_false_negative_costs_more_than_false_positive():
    only_fn = business_metrics([1, 0], [0, 0])["cost"]      # 1 falso negativo en 2
    only_fp = business_metrics([0, 0], [1, 0])["cost"]      # 1 falso positivo en 2
    assert (only_fn, only_fp) == (2.5, 0.5)


def test_baselines_match_the_business_case():
    y = np.array([1] * 692 + [0] * 308)                      # 69,2 % pierde el curso
    assert business_metrics(y, np.ones(1000))["cost"] == pytest.approx(0.308)   # avisar a todos
    assert business_metrics(y, np.zeros(1000))["cost"] == pytest.approx(3.46)   # nunca avisar


def test_undefined_ratios_are_nan_not_zero():
    m = business_metrics([1, 1, 0], [1, 1, 1])               # no tranquiliza a nadie: NPV no existe
    assert np.isnan(m["npv"])
    assert business_metrics([0, 0], [0, 0])["recall_fail"] != 0     # nadie pierde el curso: recall no existe
    assert np.isnan(business_metrics([0, 0], [0, 0])["recall_fail"])


def test_threshold_and_decision():
    assert decision_threshold() == pytest.approx(1 / 6)
    assert decision_threshold(fn_cost=1, fp_cost=1) == 0.5
    assert decide_alert([0.17, 0.16, 0.5, 1 / 6]).tolist() == [True, False, True, True]   # en el umbral: se avisa


def test_metrics_from_proba_uses_the_business_decision():
    p = np.array([0.9, 0.8, 0.1, 0.3, 0.05, 0.02, 0.01, 0.0, 0.1, 0.1])
    m = metrics_from_proba(Y, p)
    assert m["tp"] == 2 and m["fp"] == 1 and m["fn"] == 1      # alerta con p >= 1/6
    assert m["roc_auc"] > 0.9 and 0 < m["pr_auc_fail"] <= 1 and m["log_loss"] > 0


def test_encode_target():
    assert encode_target(pd.Series(["Fail", "Pass", "Fail"])).tolist() == [1, 0, 1]
    with pytest.raises(ValueError):
        encode_target(pd.Series(["Fail", "Aprobado"]))


def test_make_folds_cover_everything_once_and_stratify():
    y = pd.Series(["Fail"] * 70 + ["Pass"] * 30, index=[f"S{i}" for i in range(100)])
    folds = make_folds(y, n_splits=5, seed=42)
    valid = np.concatenate([va for _, va in folds])
    assert sorted(valid) == list(range(100))                   # cada fila se valida una sola vez
    for tr, va in folds:
        assert set(tr).isdisjoint(va)
        assert (y.iloc[va] == "Fail").mean() == pytest.approx(0.7, abs=0.02)
    again = make_folds(y, n_splits=5, seed=42)
    assert all((a[1] == b[1]).all() for a, b in zip(folds, again))   # reproducible


def test_make_folds_rejects_repeated_ids():
    y = pd.Series(["Fail", "Pass"] * 10, index=["S1"] * 20)
    with pytest.raises(ValueError):
        make_folds(y)


def _toy_xy():
    X = make_students(60)
    y = np.array([1, 0, 1] * 20)
    return X, y


def test_pipeline_fits_with_missing_values_and_predicts_probabilities():
    X, y = _toy_xy()
    pipe = build_pipeline(LogisticRegression(max_iter=200), scale=True).fit(X, y)
    p = pipe.predict_proba(X)[:, 1]
    assert p.shape == (60,) and ((p >= 0) & (p <= 1)).all()


def test_pipeline_with_engineered_feature_handles_zero_hours():
    X, y = _toy_xy()
    X.loc[3, "study_hours_per_day"] = 0.0                       # cociente con denominador 0 -> vacío, no infinito
    pipe = build_pipeline(LogisticRegression(max_iter=200), engineered=["self_study_share", "prep_total_hours"], scale=True)
    assert np.isfinite(pipe.fit(X, y).predict_proba(X)).all()


def test_evaluate_folds_returns_one_row_per_fold_with_all_metrics():
    X, y = _toy_xy()
    folds = make_folds(pd.Series(y), n_splits=3)
    res = evaluate_folds(build_pipeline(DummyClassifier(strategy="prior")), X.reset_index(drop=True), y, folds)
    assert len(res) == 3
    assert {"cost", "recall_fail", "npv", "pr_auc_fail", "log_loss", "fit_seconds"} <= set(res.columns)


def test_evaluate_folds_refuses_the_target_inside_x():
    X, y = _toy_xy()
    X["pass_70"] = np.where(y == 1, "Fail", "Pass")
    with pytest.raises(ValueError):
        evaluate_folds(build_pipeline(DummyClassifier()), X, y, make_folds(pd.Series(y), n_splits=3))


def test_top_k_alert_picks_the_most_risky_and_respects_capacity():
    p = np.array([0.1, 0.9, 0.5, 0.7, 0.2, 0.3, 0.8, 0.4, 0.6, 0.0])
    alert = top_k_alert(p, 30)
    assert alert.sum() == 3 and set(np.flatnonzero(alert)) == {1, 6, 3}     # los 3 con mayor P(Fail)
    assert top_k_alert(p, 100).all() and not top_k_alert(p, 0).any()


def test_metrics_from_proba_includes_top_k_and_argmax_cost():
    p = np.array([0.9, 0.8, 0.1, 0.3, 0.05, 0.02, 0.01, 0.0, 0.1, 0.1])
    m = metrics_from_proba(Y, p)
    assert m["precision_top30"] == pytest.approx(2 / 3) and m["recall_top30"] == pytest.approx(2 / 3)   # avisa a 3: [0.9, 0.8, 0.3]
    assert m["cost_argmax"] == pytest.approx(0.5)     # a mano: con p >= 0,5 avisa a 2 (VP = 2, FN = 1, FP = 0) -> 5 / 10
    assert m["cost"] == pytest.approx(0.6)            # con p >= 1/6 avisa a 3 (VP = 2, FN = 1, FP = 1) -> 6 / 10


def test_candidates_have_a_baseline_and_the_four_models_and_are_reproducible():
    c = candidates()
    assert list(c)[0].startswith("línea base") and len(c) == 5
    assert all(hasattr(model, "fit") for model, _ in c.values())
    assert c["regresión logística"][1] is True and c["random forest"][1] is False   # solo el lineal pide escalar


def test_baseline_is_alert_everyone_and_costs_the_fail_rate_complement():
    X, y = _toy_xy()
    baseline, _ = candidates()["línea base (avisar a todos)"]
    p = build_pipeline(baseline).fit(X, y).predict_proba(X)[:, 1]
    m = metrics_from_proba(y, p)
    assert m["alerts_per_100"] == 100 and m["recall_fail"] == 1.0
    assert m["cost"] == pytest.approx(1 - y.mean())            # solo cuesta avisar a quienes habrían aprobado


def test_top_k_precision_and_recall_are_not_mixed_up():
    y = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])                          # 4 de 10 pierden el curso
    p = np.array([0.9, 0.8, 0.7, 0.1, 0.2, 0.05, 0.0, 0.0, 0.0, 0.0])      # el 30 % superior son 3 estudiantes, los 3 pierden
    m = metrics_from_proba(y, p)
    assert m["precision_top30"] == pytest.approx(1.0)                      # 3 de 3 alertas acertaron
    assert m["recall_top30"] == pytest.approx(0.75)                        # se detectó a 3 de los 4 que pierden
    assert m["cost_top30"] == pytest.approx(5 * 1 / 10)                    # un falso negativo cuesta 5, de 10 estudiantes
