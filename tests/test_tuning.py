"""Pruebas de la optimización (`src/proyecto/models/tuning.py`): espacio de búsqueda, estudio de Optuna e intervalos."""
import mlflow
import numpy as np
import optuna
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score
from toy import make_students

from proyecto.data.split import make_folds
from proyecto.models.train import build_pipeline, evaluate_folds
from proyecto.models.tuning import (C_RANGE, MODELS, OBJETIVOS, THRESHOLD_RANGE, bootstrap_cost_difference,
                                    bootstrap_metric_ci, lr_space, make_lr, row_costs, tune)


def _toy_xy(n: int = 90):
    X = make_students(n)
    rng = np.random.default_rng(1)
    X["previous_exam_score"] = rng.normal(70, 10, n)
    y = (X["previous_exam_score"] + rng.normal(0, 5, n) < 70).astype(int)     # señal real: nota previa baja -> pierde
    return X, y


def test_row_costs_by_hand():
    y = [1, 1, 0, 0]
    alert = [1, 0, 1, 0]
    assert row_costs(y, alert).tolist() == [0, 5, 1, 0]          # acierto, falso negativo (5), falso positivo (1), acierto


def test_search_space_has_c_and_threshold_inside_documented_ranges():
    params = lr_space(optuna.trial.FixedTrial({"C": 0.5, "threshold": 0.2}))
    assert params == {"C": 0.5, "threshold": 0.2}
    assert C_RANGE[0] < 0.5 < C_RANGE[1] and THRESHOLD_RANGE[0] < 0.2 < THRESHOLD_RANGE[1]
    assert "threshold" not in lr_space(optuna.trial.FixedTrial({"C": 0.5}), tune_threshold=False)


def test_make_lr_ignores_the_threshold_because_it_is_not_a_model_parameter():
    model = make_lr({"C": 0.3, "threshold": 0.2})
    assert model.C == 0.3 and model.max_iter == 1000


def test_tune_runs_the_budget_and_stays_inside_the_ranges():
    X, y = _toy_xy()
    study = tune("regresión logística", X, y, make_folds(pd.Series(y), 3), n_trials=4, log=False)
    assert len(study.trials) == 4
    assert C_RANGE[0] <= study.best_params["C"] <= C_RANGE[1]
    assert THRESHOLD_RANGE[0] <= study.best_params["threshold"] <= THRESHOLD_RANGE[1]
    assert study.best_value == min(t.value for t in study.trials)          # costo: menor es mejor


def test_threshold_free_metric_does_not_search_the_threshold():
    X, y = _toy_xy()
    study = tune("regresión logística", X, y, make_folds(pd.Series(y), 3), n_trials=2, log=False, metric="log_loss")
    assert set(study.best_params) == {"C"}


def test_tune_rejects_unknown_metric_and_model():
    X, y = _toy_xy()
    folds = make_folds(pd.Series(y), 3)
    with pytest.raises(ValueError):
        tune("regresión logística", X, y, folds, n_trials=1, log=False, metric="no_existe")
    with pytest.raises(ValueError):
        tune("lightgbm", X, y, folds, n_trials=1, log=False)
    assert set(MODELS) == {"regresión logística"} and "cost" in OBJETIVOS


def test_study_resumes_from_disk_and_only_runs_the_missing_trials(tmp_path):
    X, y = _toy_xy()
    folds = make_folds(pd.Series(y), 3)
    db = tmp_path / "estudio.db"
    first = tune("regresión logística", X, y, folds, n_trials=2, log=False, storage=str(db))
    assert len(first.trials) == 2
    again = tune("regresión logística", X, y, folds, n_trials=2, log=False, storage=str(db))
    assert len(again.trials) == 2                                          # ya estaban hechos: no se repite nada
    more = tune("regresión logística", X, y, folds, n_trials=3, log=False, storage=str(db))
    assert len(more.trials) == 3                                           # solo falta uno


def test_every_trial_is_logged_in_mlflow_as_a_nested_run(tmp_path):
    X, y = _toy_xy()
    mlflow.set_tracking_uri(f"sqlite:///{(tmp_path / 'm.db').as_posix()}")
    mlflow.set_experiment("prueba-tuning")
    study = tune("regresión logística", X, y, make_folds(pd.Series(y), 3), n_trials=3, log=True)
    runs = mlflow.search_runs(experiment_names=["prueba-tuning"])
    trials = runs[runs["tags.mlflow.runName"].str.contains("-trial-")]
    assert len(trials) == 3 and "metrics.cost" in runs.columns and "params.C" in runs.columns
    assert study.user_attrs["mlflow_parent_run_id"] in set(runs["run_id"])


def test_bootstrap_difference_is_zero_for_the_same_model():
    y = np.array([1, 0, 1, 0, 1, 1, 0, 0] * 25)
    p = np.random.default_rng(0).random(len(y))
    diff, low, high = bootstrap_cost_difference(y, p, p)
    assert diff == 0 and low == 0 and high == 0


def test_bootstrap_difference_detects_a_clearly_better_model_and_is_reproducible():
    rng = np.random.default_rng(0)
    y = (rng.random(600) < 0.5).astype(int)
    good = np.where(y == 1, 0.9, 0.05)                      # separa perfecto
    bad = rng.random(600)                                    # azar
    diff, low, high = bootstrap_cost_difference(y, good, bad)
    assert diff < 0 and high < 0                              # A (bueno) cuesta menos con confianza del 95 %
    assert low <= diff <= high                                # el intervalo está ordenado y contiene la diferencia
    assert bootstrap_cost_difference(y, good, bad) == (diff, low, high)


def test_bootstrap_difference_uses_each_models_own_threshold():
    y = np.array([1, 1, 0, 0] * 50)
    p = np.array([0.30, 0.30, 0.10, 0.10] * 50)
    same, _, _ = bootstrap_cost_difference(y, p, p, threshold_a=0.2, threshold_b=0.2)
    higher, _, _ = bootstrap_cost_difference(y, p, p, threshold_a=0.5, threshold_b=0.2)   # 0,5 no avisa a nadie
    assert same == 0 and higher == pytest.approx(5 * 0.5)     # no avisar a quien pierde (50 %) cuesta 5 por estudiante


def test_bootstrap_metric_ci_contains_the_value_and_is_ordered():
    rng = np.random.default_rng(3)
    y = (rng.random(400) < 0.5).astype(int)
    p = np.clip(y * 0.4 + rng.random(400) * 0.6, 0, 1)
    value, low, high = bootstrap_metric_ci(y, p, roc_auc_score, n_boot=100)
    assert low <= value <= high and 0.5 < value <= 1


def test_each_trial_is_scored_with_its_own_threshold():
    X, y = _toy_xy()
    folds = make_folds(pd.Series(y), 3)
    study = tune("regresión logística", X, y, folds, n_trials=1, log=False)
    params = study.best_params
    expected = evaluate_folds(build_pipeline(make_lr(params), scale=True), X, y, folds, threshold=params["threshold"])["cost"].mean()
    ignoring_threshold = evaluate_folds(build_pipeline(make_lr(params), scale=True), X, y, folds)["cost"].mean()
    assert study.best_value == pytest.approx(expected)                     # el costo del ensayo usa el umbral sugerido
    assert abs(expected - ignoring_threshold) > 1e-9                       # y ese umbral sí cambia el costo (la prueba es sensible)


def test_c_is_searched_on_a_logarithmic_scale():
    X, y = _toy_xy()
    study = tune("regresión logística", X, y, make_folds(pd.Series(y), 3), n_trials=1, log=False)
    assert study.trials[0].distributions["C"].log is True                  # C cambia en órdenes de magnitud
