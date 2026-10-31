"""Pruebas de la partición: sin pérdida de filas, sin cruce entre lados y con la misma proporción de `Fail`."""
import numpy as np
import pandas as pd
import pytest

from proyecto.data.cleaning import TARGET
from proyecto.data.split import split_train_test


def toy(n: int = 1000, fail_rate: float = 0.692) -> pd.DataFrame:
    """Estudiantes de juguete con la misma proporción de `Fail` (< 70) que el dataset real, índice = student_id."""
    n_fail = int(n * fail_rate)
    target = np.array(["Fail"] * n_fail + ["Pass"] * (n - n_fail))
    return pd.DataFrame({"x": np.arange(n), TARGET: target}, index=[f"STU_{i}" for i in range(n)])


def fail_gap(train: pd.DataFrame, test: pd.DataFrame) -> float:
    """Diferencia (en proporción) entre el % de Fail del entrenamiento y el de la prueba."""
    return abs((train[TARGET] == "Fail").mean() - (test[TARGET] == "Fail").mean())


def test_no_rows_are_lost_or_repeated():
    df = toy()
    train, test = split_train_test(df)
    assert len(train) + len(test) == len(df)
    assert set(train.index) | set(test.index) == set(df.index)


def test_no_student_is_on_both_sides():
    train, test = split_train_test(toy())
    assert set(train.index).isdisjoint(set(test.index))


def test_test_size_is_respected():
    train, test = split_train_test(toy(1000), test_size=0.2)
    assert len(test) == 200 and len(train) == 800


def test_fail_proportion_is_the_same_on_both_sides():
    df = toy()
    train, test = split_train_test(df)
    overall = (df[TARGET] == "Fail").mean()
    assert fail_gap(train, test) < 0.005
    assert abs((train[TARGET] == "Fail").mean() - overall) < 0.005


def test_same_seed_gives_the_same_split():
    a_train, _ = split_train_test(toy(), seed=42)
    b_train, _ = split_train_test(toy(), seed=42)
    assert a_train.index.equals(b_train.index)


def test_the_fail_proportion_check_does_detect_a_bad_split():
    """Esta prueba existe para comprobar que la comprobación PUEDE fallar: con una partición mala sí falla."""
    df = toy().sort_values(TARGET)                      # partición sin mezclar: todos los Fail quedan juntos
    cut = int(len(df) * 0.8)
    bad_train, bad_test = df.iloc[:cut], df.iloc[cut:]
    assert fail_gap(bad_train, bad_test) > 0.2


def test_split_fails_with_repeated_ids():
    dirty = toy()
    dirty.index = ["STU_0"] + list(dirty.index[1:-1]) + ["STU_0"]      # un estudiante repetido
    with pytest.raises(ValueError):
        split_train_test(dirty)


def test_split_requires_the_target():
    with pytest.raises(KeyError):
        split_train_test(toy().drop(columns=[TARGET]))
