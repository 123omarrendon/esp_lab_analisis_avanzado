"""Pruebas de la validación final (`src/proyecto/models/validation.py`): calibración, prueba abierta una vez, grupos."""
import json

import numpy as np
import pandas as pd
import pytest
from toy import make_students

from proyecto.models.tuning import make_lr
from proyecto.models.train import build_pipeline
from proyecto.models.validation import (age_band, coefficient_table, decide_calibration, freeze_decisions,
                                        metric_with_ci, open_test_once, segment_table, shap_importance,
                                        student_contributions)


# ---------- calibración: regla escrita antes de mirar ----------
def test_calibrates_only_when_log_loss_improves_and_cost_does_not_worsen():
    assert decide_calibration(0.40, 0.38, cost_diff_low=-0.01) is True          # mejora clara, costo no empeora
    assert decide_calibration(0.40, 0.397, cost_diff_low=-0.01) is False        # mejora menor a 0,005: no vale la pena
    assert decide_calibration(0.40, 0.38, cost_diff_low=0.002) is False         # el costo empeora con confianza
    assert decide_calibration(0.40, 0.38, cost_diff_low=0.0) is True            # un intervalo que toca el cero no es «empeora»
    assert decide_calibration(0.40, 0.42, cost_diff_low=-0.01) is False         # el log loss empeora


# ---------- decisiones congeladas ----------
def test_freeze_writes_timestamp_and_does_not_overwrite_after_test_opened(tmp_path):
    path = tmp_path / "decisiones.json"
    first = freeze_decisions({"modelo": "A"}, path, test_opened=False)
    assert "fecha_y_hora" in first and first["modelo"] == "A"
    again = freeze_decisions({"modelo": "B"}, path, test_opened=True)           # la prueba ya se abrió: no se reescribe
    assert again["modelo"] == "A" and json.loads(path.read_text(encoding="utf-8"))["modelo"] == "A"
    rewritten = freeze_decisions({"modelo": "C"}, path, test_opened=False)      # antes de abrir sí se puede ajustar
    assert rewritten["modelo"] == "C"


# ---------- la prueba se abre una sola vez ----------
def test_test_is_evaluated_only_once_and_marker_is_written(tmp_path):
    marker, cache = tmp_path / "abierta.txt", tmp_path / "cache.joblib"
    calls = []

    def predict():
        calls.append(1)
        return np.array([0.1, 0.9])

    first, opened_now = open_test_once(marker, cache, predict, note="modelo X.")
    assert opened_now and len(calls) == 1 and marker.exists() and "modelo X." in marker.read_text(encoding="utf-8")
    second, opened_again = open_test_once(marker, cache, predict)
    assert not opened_again and len(calls) == 1                                 # NO se volvió a evaluar con la prueba
    assert second.tolist() == first.tolist()


def test_reopening_without_saved_results_fails_loudly(tmp_path):
    marker, cache = tmp_path / "abierta.txt", tmp_path / "cache.joblib"
    marker.write_text("abierta", encoding="utf-8")
    with pytest.raises(RuntimeError, match="declararlo"):
        open_test_once(marker, cache, lambda: 1)


# ---------- intervalo de una métrica ----------
def test_metric_with_ci_cost_by_hand_and_interval_contains_value():
    y = np.array([1, 1, 0, 0] * 50)
    p = np.array([0.9, 0.05, 0.9, 0.05] * 50)       # umbral 1/6: acierta, falso negativo (5), falso positivo (1), acierto
    value, low, high = metric_with_ci(y, p, threshold=1 / 6, key="cost", n_boot=200)
    assert value == pytest.approx((5 + 1) / 4)       # (5 + 1) por cada 4 estudiantes
    assert low <= value <= high
    recall, _, _ = metric_with_ci(y, p, threshold=1 / 6, key="recall_fail", n_boot=50)
    assert recall == pytest.approx(0.5)


# ---------- grupos ----------
def test_age_band_separates_minors_by_hand():
    bands = age_band(pd.Series([14, 15, 16, 17, 18, 20]))
    assert bands.tolist() == ["≤15", "≤15", "16–17", "16–17", "≥18", "≥18"]


def test_segment_table_by_hand():
    y = [1, 1, 0, 0, 1, 0]
    p = [0.9, 0.05, 0.9, 0.05, 0.9, 0.05]            # alerta: sí, no, sí, no, sí, no
    groups = pd.DataFrame({"g": ["a", "a", "a", "a", "b", "b"]})
    table = segment_table(y, p, threshold=1 / 6, groups=groups, columns=["g"])
    a, b = table.loc[("g", "a")], table.loc[("g", "b")]
    assert a["casos"] == 4 and a["recall Fail"] == pytest.approx(0.5) and a["% alertas"] == pytest.approx(50)
    assert a["costo"] == pytest.approx((5 + 1) / 4)
    assert b["casos"] == 2 and b["recall Fail"] == pytest.approx(1.0) and b["% Fail real"] == pytest.approx(50)
    assert table["casos"].sum() == len(y)            # ningún estudiante se pierde ni se cuenta dos veces


def test_segment_table_marks_uncomputable_ratio_as_nan_not_zero():
    table = segment_table([1, 1], [0.9, 0.9], threshold=1 / 6, groups=pd.DataFrame({"g": ["a", "a"]}), columns=["g"])
    assert np.isnan(table.loc[("g", "a"), "NPV"])    # nadie quedó tranquilo: el NPV no existe, no es 0


def test_segment_table_rejects_misaligned_groups():
    with pytest.raises(ValueError, match="misma longitud"):
        segment_table([1, 0], [0.9, 0.1], threshold=0.5, groups=pd.DataFrame({"g": ["a"]}), columns=["g"])


# ---------- interpretación ----------
def _fitted_toy_pipeline(n: int = 120):
    X = make_students(n)
    rng = np.random.default_rng(1)
    X["previous_exam_score"] = rng.normal(70, 10, n)
    y = (X["previous_exam_score"] + rng.normal(0, 5, n) < 70).astype(int)
    return build_pipeline(make_lr({"C": 1.0}), scale=True).fit(X, y), X


def test_coefficient_table_sorted_by_size_and_signal_points_to_fail():
    pipeline, _ = _fitted_toy_pipeline()
    table = coefficient_table(pipeline)
    assert table["coeficiente"].abs().is_monotonic_decreasing
    assert table.loc["previous_exam_score", "coeficiente"] < 0      # nota previa alta -> menos probable perder
    assert np.allclose(table["odds ratio"], np.exp(table["coeficiente"]))


def test_shap_importance_ranks_the_real_signal_first():
    pipeline, X = _fitted_toy_pipeline()
    importance = shap_importance(pipeline, X.head(60))
    assert importance.index[0] == "previous_exam_score"
    assert (importance["|SHAP| medio"] >= 0).all()


def test_student_contributions_add_up_to_the_model_logit():
    pipeline, X = _fitted_toy_pipeline()
    row = X.head(1)
    full = student_contributions(pipeline, row, top=1000)
    model = pipeline.named_steps["model"]
    logit = full["contribución al logit"].sum() + float(model.intercept_[0])
    assert logit == pytest.approx(float(pipeline.decision_function(row)[0]))        # suma de partes = predicción
    assert student_contributions(pipeline, row, top=3).shape[0] == 3
    with pytest.raises(ValueError, match="exactamente un estudiante"):
        student_contributions(pipeline, X.head(2))
