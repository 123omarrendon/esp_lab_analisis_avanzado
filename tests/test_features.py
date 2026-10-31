"""Pruebas de las variables y el preprocesamiento de la etapa 4 (`src/proyecto/features/engineering.py`).

Los casos son pequeños y hechos a mano: se puede comprobar con calculadora lo que debe salir.
"""
import numpy as np
import pandas as pd
import pytest

from toy import make_students

from proyecto.features.engineering import (
    CATEGORICAL_BASE, ENGINEERED_FEATURES, NO_SIGNAL_COLUMNS, NUMERIC_BASE, STAGE4_ADD_MISSING_INDICATOR, STAGE4_DROP, TIMING_COLUMNS,
    add_features, build_preprocessor, feature_columns,
)

# Escritas a mano a propósito (no importadas del código): si alguien las cuela en las variables, la prueba falla.
FORBIDDEN = {"exam_score", "pass_status", "performance_grade", "performance_level", "questions_correct",
             "questions_attempted", "student_id", "gender", "family_income", "pass_70"}


def test_base_columns_are_the_35_variables_of_stage_3():
    assert (len(NUMERIC_BASE), len(CATEGORICAL_BASE)) == (19, 16)
    assert len(set(NUMERIC_BASE) | set(CATEGORICAL_BASE)) == 35


def test_no_forbidden_column_is_a_feature():
    numeric, categorical = feature_columns(engineered=ENGINEERED_FEATURES)
    assert not FORBIDDEN & set(numeric + categorical)


def test_special_groups_are_real_columns():
    assert set(TIMING_COLUMNS) | set(NO_SIGNAL_COLUMNS) <= set(NUMERIC_BASE) | set(CATEGORICAL_BASE)
    assert len(NO_SIGNAL_COLUMNS) == 7 and len(TIMING_COLUMNS) == 3


def test_stage4_proposal_keeps_28_variables_and_the_exam_difficulty():
    numeric, categorical = feature_columns(drop=STAGE4_DROP)
    assert len(numeric) + len(categorical) == 28
    assert "exam_difficulty" in categorical and not set(NO_SIGNAL_COLUMNS) & set(numeric)
    assert STAGE4_ADD_MISSING_INDICATOR is False


def test_feature_columns_drop_and_engineered():
    numeric, categorical = feature_columns(drop=TIMING_COLUMNS, engineered=["self_study_share"])
    assert "exam_difficulty" not in categorical and len(categorical) == 15
    assert "time_management_score" not in numeric and "exam_anxiety_level" not in numeric
    assert numeric[-1] == "self_study_share" and len(numeric) == 17 + 1


def test_unknown_names_fail_loudly():
    with pytest.raises(ValueError):
        feature_columns(drop=["no_existe"])
    with pytest.raises(ValueError):
        feature_columns(engineered=["no_existe"])
    with pytest.raises(ValueError):
        add_features(make_students(), engineered=["no_existe"])


def test_self_study_share_is_a_ratio_not_a_sum():
    df = pd.DataFrame({"self_study_hours": [2.0, 3.0], "study_hours_per_day": [4.0, 3.0],
                       "exam_preparation_days": [1.0, 1.0]})
    out = add_features(df, engineered=["self_study_share"])
    assert out["self_study_share"].tolist() == [0.5, 1.0]          # 2/4 y 3/3, no 6 ni 7


def test_ratio_with_zero_or_missing_denominator_is_nan_not_infinite():
    df = pd.DataFrame({"self_study_hours": [0.0, 1.0, 2.0], "study_hours_per_day": [0.0, np.nan, 4.0],
                       "exam_preparation_days": [1.0, 1.0, 1.0]})
    share = add_features(df, engineered=["self_study_share"])["self_study_share"]
    assert share.isna().tolist() == [True, True, False]
    assert not np.isinf(share.dropna()).any()


def test_prep_total_hours_is_hours_times_days():
    df = pd.DataFrame({"self_study_hours": [1.0], "study_hours_per_day": [3.0], "exam_preparation_days": [7.0]})
    assert add_features(df, engineered=["prep_total_hours"])["prep_total_hours"].iloc[0] == 21.0


def test_add_features_does_not_modify_the_original():
    df = make_students()
    before = df.copy()
    out = add_features(df)
    pd.testing.assert_frame_equal(df, before)
    assert set(ENGINEERED_FEATURES) <= set(out.columns) and not set(ENGINEERED_FEATURES) & set(df.columns)


def test_add_features_only_adds_what_is_asked():
    out = add_features(make_students(), engineered=["self_study_share"])
    assert "self_study_share" in out.columns and "prep_total_hours" not in out.columns


def test_preprocessor_leaves_no_missing_and_adds_indicator_only_where_train_had_missing():
    df = make_students()
    prep = build_preprocessor().fit(df)
    out = prep.transform(df)
    assert not np.isnan(out).any()
    without_indicator = build_preprocessor(add_missing_indicator=False).fit(df).transform(df)
    assert out.shape[1] == without_indicator.shape[1] + 1       # solo previous_gpa tenía vacíos


def test_median_comes_from_training_only():
    train = make_students()
    train["previous_gpa"] = [1.0, 2.0, 3.0] + [2.0] * 37         # mediana del entrenamiento = 2
    train.loc[0, "previous_gpa"] = 1.0
    new = make_students(4)
    new["previous_gpa"] = [100.0, 100.0, 100.0, np.nan]            # la mediana de estos sería 100
    prep = build_preprocessor(add_missing_indicator=False).fit(train)
    numeric = list(feature_columns()[0])
    col = numeric.index("previous_gpa")
    assert prep.transform(new)[3, col] == 2.0                      # se rellena con la mediana del ENTRENAMIENTO


def test_unseen_category_and_missing_category_do_not_fail():
    train = make_students()
    new = make_students(4)
    new["school_type"] = "Z"                                       # categoría que el entrenamiento nunca vio
    new.loc[0, "parent_education"] = np.nan
    out = build_preprocessor().fit(train).transform(new)
    assert not np.isnan(out).any()


def test_missing_category_gets_its_own_column():
    df = make_students()
    prep = build_preprocessor().fit(df)
    names = prep.get_feature_names_out()
    assert "cat__parent_education_Desconocido" in names


def test_extra_columns_are_dropped_not_used():
    df = make_students()
    leaky = df.assign(exam_score=np.arange(len(df), dtype=float), gender="X")
    clean_out = build_preprocessor().fit(df).transform(df)
    leaky_out = build_preprocessor().fit(leaky).transform(leaky)
    np.testing.assert_array_equal(clean_out, leaky_out)            # una columna de fuga extra no cambia nada


def test_scale_only_when_asked():
    df = make_students()
    plain = build_preprocessor(scale=False).fit(df).transform(df)
    scaled = build_preprocessor(scale=True).fit(df).transform(df)
    names = build_preprocessor(scale=True).fit(df).get_feature_names_out()
    col = list(names).index("num__study_hours_per_day")
    assert abs(scaled[:, col].mean()) < 1e-9 or scaled[:, col].std() == 0   # centrada (o constante en el juguete)
    assert plain.shape == scaled.shape
