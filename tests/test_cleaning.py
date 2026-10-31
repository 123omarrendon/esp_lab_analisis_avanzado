"""Pruebas de la limpieza (una por decisión del EDA), con casos hechos a mano: uno normal y uno sucio.

Regla del caso: aprueba con 70 o más; con menos de 70 (69, 69,99) pierde el curso.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proyecto.data.cleaning import (
    ID_COL,
    LEAK_COLUMNS,
    PASS_THRESHOLD,
    TARGET,
    add_target,
    check_missing_report,
    clean,
    drop_identifier,
    drop_leakage_columns,
    drop_sensitive_columns,
    extract_audit_columns,
    load_raw,
    mark_out_of_range,
)

CSV = Path(__file__).resolve().parents[1] / "data" / "student_exam_performance.csv"

# Escritas a mano a propósito: si se compararan con LEAK_COLUMNS, una columna olvidada en el código pasaría desapercibida.
SIX_LEAK_COLUMNS = {"exam_score", "pass_status", "performance_grade", "performance_level",
                    "questions_correct", "questions_attempted"}


def toy() -> pd.DataFrame:
    """Cuatro estudiantes. El 2.º saca 69 (pierde con 70 aunque `pass_status`, con corte en 50, diga Pass) y el 4.º saca 70."""
    return pd.DataFrame({
        "student_id": ["STU_1", "STU_2", "STU_3", "STU_4"],
        "gender": ["Female", "Male", "Other", "Male"],
        "family_income": ["Low", "High", "Middle", "Low"],
        "urban_rural": ["Urban", "Rural", "Urban", "Suburban"],
        "previous_exam_score": [70.0, 55.0, 90.0, 40.0],
        "previous_gpa": [3.0, np.nan, 3.8, 2.0],
        "attendance_percentage": [90.0, 80.0, np.nan, 70.0],
        "study_hours_per_day": [3.0, 12.0, 1.0, 2.0],
        "exam_score": [80.0, 69.0, 95.0, 70.0],
        "pass_status": ["Pass", "Pass", "Pass", "Pass"],          # corte en 50: todos aprueban
        "performance_grade": ["B", "C", "A", "C"],
        "performance_level": ["High", "Medium", "High", "Medium"],
        "questions_correct": [80, 69, 95, 70],
        "questions_attempted": [100, 100, 100, 100],
    })


# --- add_target (la regla de 70) ---------------------------------------------------------------------------

def test_pass_threshold_is_70():
    assert PASS_THRESHOLD == 70 and TARGET == "pass_70"


def test_add_target_applies_the_70_rule_on_a_normal_case():
    out = add_target(toy())
    assert out[TARGET].tolist() == ["Pass", "Fail", "Pass", "Pass"]       # 80 Pass, 69 Fail, 95 Pass, 70 Pass


def test_add_target_boundary_69_fails_and_70_passes():
    edge = pd.DataFrame({"exam_score": [0.0, 69.0, 69.99, 70.0, 70.01, 100.0]})
    assert add_target(edge)[TARGET].tolist() == ["Fail", "Fail", "Fail", "Pass", "Pass", "Pass"]


def test_add_target_is_not_the_dataset_pass_status():
    """El estudiante con 69 aprobaba con el corte de 50 (pass_status) y pierde con 70: el objetivo NO es pass_status."""
    out = add_target(toy())
    assert (out["pass_status"] == "Pass").all() and (out[TARGET] == "Fail").any()


def test_add_target_does_not_modify_the_original():
    raw = toy()
    add_target(raw)
    assert TARGET not in raw.columns


def test_add_target_requires_exam_score():
    with pytest.raises(KeyError):
        add_target(toy().drop(columns=["exam_score"]))


def test_add_target_fails_when_a_score_is_missing():
    dirty = toy()
    dirty.loc[0, "exam_score"] = np.nan
    with pytest.raises(ValueError):
        add_target(dirty)


# --- drop_identifier ---------------------------------------------------------------------------------------

def test_drop_identifier_moves_id_to_index():
    out = drop_identifier(toy())
    assert ID_COL not in out.columns
    assert list(out.index) == ["STU_1", "STU_2", "STU_3", "STU_4"]


def test_drop_identifier_fails_with_repeated_ids():
    dirty = toy()
    dirty.loc[1, ID_COL] = "STU_1"          # caso sucio: un estudiante repetido
    with pytest.raises(ValueError):
        drop_identifier(dirty)


def test_drop_identifier_is_idempotent():
    once = drop_identifier(toy())
    assert drop_identifier(once).equals(once)


# --- drop_leakage_columns ----------------------------------------------------------------------------------

def test_drop_leakage_columns_removes_the_six_and_keeps_target():
    out = drop_leakage_columns(add_target(toy()))
    assert not SIX_LEAK_COLUMNS & set(out.columns)
    assert set(LEAK_COLUMNS) == SIX_LEAK_COLUMNS     # la lista del código es exactamente la de las 6 columnas
    assert TARGET in out.columns
    assert "previous_exam_score" in out.columns      # lo legítimo se conserva


def test_drop_leakage_columns_ignores_columns_that_do_not_exist():
    out = drop_leakage_columns(toy().drop(columns=["questions_correct"]))
    assert "questions_correct" not in out.columns


# --- mark_out_of_range -------------------------------------------------------------------------------------

def test_mark_out_of_range_keeps_values_inside_the_range():
    out = mark_out_of_range(toy())
    assert out["previous_exam_score"].tolist() == [70.0, 55.0, 90.0, 40.0]
    assert out.loc[1, "study_hours_per_day"] == 12.0          # extremo plausible: no se recorta


def test_mark_out_of_range_turns_impossible_values_into_missing():
    dirty = toy()
    dirty.loc[0, "attendance_percentage"] = 150.0            # porcentaje imposible
    dirty.loc[1, "study_hours_per_day"] = -2.0               # horas negativas
    dirty.loc[2, "previous_gpa"] = 5.0                       # promedio fuera de 1 a 4
    out = mark_out_of_range(dirty)
    assert np.isnan(out.loc[0, "attendance_percentage"])
    assert np.isnan(out.loc[1, "study_hours_per_day"])
    assert np.isnan(out.loc[2, "previous_gpa"])
    assert len(out) == len(dirty)                            # no se borran filas


def test_mark_out_of_range_does_not_modify_the_original():
    dirty = toy()
    dirty.loc[0, "attendance_percentage"] = 150.0
    mark_out_of_range(dirty)
    assert dirty.loc[0, "attendance_percentage"] == 150.0


# --- check_missing_report ----------------------------------------------------------------------------------

def test_check_missing_report_counts_only_columns_with_missing():
    report = check_missing_report(toy())
    assert set(report.index) == {"previous_gpa", "attendance_percentage"}
    assert report.loc["previous_gpa", "missing"] == 1
    assert report.loc["previous_gpa", "missing_pct"] == 25.0


def test_check_missing_report_is_empty_when_there_are_no_missing():
    assert check_missing_report(toy().dropna(axis=1)).empty


# --- columnas sensibles ------------------------------------------------------------------------------------

def test_drop_sensitive_columns_removes_gender_and_family_income():
    out = drop_sensitive_columns(toy())
    assert "gender" not in out.columns and "family_income" not in out.columns
    assert "urban_rural" in out.columns


def test_extract_audit_columns_keeps_the_same_index():
    data = drop_identifier(toy())
    audit = extract_audit_columns(data)
    assert audit.index.equals(data.index)
    assert {"gender", "family_income", "urban_rural"} <= set(audit.columns)
    assert "previous_exam_score" not in audit.columns


# --- clean (todo junto) ------------------------------------------------------------------------------------

def test_clean_keeps_every_row_creates_the_target_and_removes_the_leaks():
    raw = toy()
    out = clean(raw)
    assert len(out) == len(raw)
    assert ID_COL not in out.columns
    assert not SIX_LEAK_COLUMNS & set(out.columns)
    assert out[TARGET].tolist() == ["Pass", "Fail", "Pass", "Pass"]        # el objetivo se creó ANTES de quitar exam_score


def test_no_personal_columns_in_the_features():
    features = drop_sensitive_columns(clean(toy()))
    assert not {ID_COL, "gender", "family_income"} & set(features.columns)


def test_clean_requires_exam_score_to_build_the_target():
    with pytest.raises(KeyError):
        clean(toy().drop(columns=["exam_score"]))


# --- con el dataset real (se omite si el CSV no está) -----------------------------------------------------

@pytest.mark.skipif(not CSV.exists(), reason="data/student_exam_performance.csv no está en el repo")
def test_real_dataset_target_matches_the_70_rule_and_loses_no_rows():
    raw = load_raw(CSV)
    out = clean(raw)
    assert len(out) == len(raw) == 100_000
    assert not SIX_LEAK_COLUMNS & set(out.columns)
    # Conteos medidos en el EDA: 69.210 pierden el curso (< 70) y 30.790 aprueban (>= 70).
    assert (out[TARGET] == "Fail").sum() == 69_210 and (out[TARGET] == "Pass").sum() == 30_790
    assert ((raw["exam_score"] < 70) == (out[TARGET] == "Fail")).all()
    # El EDA no encontró valores imposibles: la limpieza no debe crear vacíos nuevos.
    assert out.isna().sum().sum() == raw.drop(columns=list(SIX_LEAK_COLUMNS)).isna().sum().sum()
    assert set(check_missing_report(out).index) == {
        "attendance_percentage", "time_management_score", "notes_quality", "previous_gpa",
        "sleep_quality", "parent_education", "device_availability"}
