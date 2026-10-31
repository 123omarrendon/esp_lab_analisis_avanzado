"""Limpieza de los datos de rendimiento estudiantil (etapa 3).

Regla del caso (`notebooks/01b_caso_negocio_aprueba_o_no.ipynb`): el estudiante **aprueba con 70 o más** y
**pierde el curso con menos de 70** (69,99 pierde). El objetivo `pass_70` se deriva de `exam_score`; la columna
`pass_status` del dataset usa el corte de 50 y por eso NO es el objetivo: es una fuga más.

Cada función implementa UNA decisión de la tabla del EDA (`reports/01_eda.md`, `notebooks/02b_eda_aprueba_o_no.ipynb`)
y de `especificaciones/03-preprocesamiento.md`. Ninguna calcula medias ni medianas con los datos: imputar depende del
entrenamiento y va dentro del `Pipeline` de la etapa 4.

Orden de uso (lo hace el notebook `03b_preprocesamiento_aprueba_o_no.ipynb`):

    df = load_raw("data/student_exam_performance.csv")
    clean_df = clean(df)
    audit = extract_audit_columns(clean_df)      # se guarda aparte para auditar la equidad
    features = drop_sensitive_columns(clean_df)  # lo que verá el modelo
"""
from pathlib import Path

import numpy as np
import pandas as pd

ID_COL = "student_id"
PASS_THRESHOLD = 70             # aprueba con 70 o más; con menos de 70 pierde el curso
TARGET = "pass_70"              # "Pass" (nota >= 70) / "Fail" (nota < 70); la clase de interés es "Fail"

# Contienen la respuesta o son datos del propio examen. `exam_score` y `pass_status` (corte en 50) son versiones
# de la misma respuesta: quien reprueba con 50 siempre reprueba con 70. Se quitan DESPUÉS de crear el objetivo.
LEAK_COLUMNS = ("exam_score", "pass_status", "performance_grade", "performance_level",
                "questions_correct", "questions_attempted")

# No entran como predictores por defecto (decisión del EDA); se conservan aparte solo para auditar la equidad.
EXCLUDE_FROM_FEATURES = ("gender", "family_income")
AUDIT_COLUMNS = ("gender", "family_income", "urban_rural", "school_type", "education_level", "age")

# Rangos lógicos: lo que queda fuera se marca como vacío (no se borra la fila).
# Los extremos plausibles (12 h de estudio, 15 h en línea) NO se recortan: están dentro de estos rangos.
VALID_RANGES = {
    "previous_exam_score": (0, 100),
    "attendance_percentage": (0, 100),
    "assignment_completion_rate": (0, 100),
    "previous_gpa": (1, 4),
    "sleep_hours": (0, 24),
    "study_hours_per_day": (0, 24),
    "self_study_hours": (0, 24),
    "online_learning_hours": (0, 24),
}


def drop_identifier(df: pd.DataFrame, id_col: str = ID_COL) -> pd.DataFrame:
    """Pasa el identificador del estudiante al índice, para que no sea una variable de entrada.

    Falla si hay identificadores repetidos: el EDA mostró que son únicos y la partición por fila depende de eso.
    Si el identificador ya es el índice (o no existe), devuelve una copia sin cambios.
    """
    if id_col not in df.columns:
        return df.copy()
    if df[id_col].duplicated().any():
        raise ValueError(f"'{id_col}' tiene valores repetidos: ya no se puede partir por fila sin riesgo de fuga.")
    return df.set_index(id_col)


def load_raw(path: str | Path) -> pd.DataFrame:
    """Lee el CSV original (sin modificarlo) y deja `student_id` como índice."""
    return drop_identifier(pd.read_csv(path, low_memory=False))


def add_target(df: pd.DataFrame, threshold: float = PASS_THRESHOLD) -> pd.DataFrame:
    """Crea el objetivo `pass_70` a partir de `exam_score`: "Pass" si la nota es >= 70 y "Fail" si es < 70.

    69 y 69,99 pierden el curso; 70,00 aprueba. Falla si falta la nota o si alguna está vacía, porque
    entonces no se puede saber el resultado de ese estudiante. No modifica el original.
    """
    if "exam_score" not in df.columns:
        raise KeyError("Falta la columna 'exam_score': de ella se deriva el objetivo.")
    if df["exam_score"].isna().any():
        raise ValueError("Hay estudiantes sin nota (exam_score vacía): no se puede definir si aprueban.")
    out = df.copy()
    out[TARGET] = np.where(out["exam_score"] >= threshold, "Pass", "Fail")
    return out


def drop_leakage_columns(df: pd.DataFrame, columns: tuple[str, ...] = LEAK_COLUMNS) -> pd.DataFrame:
    """Quita las columnas que contienen la respuesta o se conocen al rendir el examen. Conserva el objetivo."""
    return df.drop(columns=[c for c in columns if c in df.columns])


def mark_out_of_range(df: pd.DataFrame, ranges: dict[str, tuple[float, float]] = VALID_RANGES) -> pd.DataFrame:
    """Vuelve vacío (NaN) todo valor fuera de su rango lógico. No borra filas ni modifica el original."""
    out = df.copy()
    for col, (low, high) in ranges.items():
        if col in out.columns:
            out[col] = out[col].astype("float64").where(out[col].between(low, high) | out[col].isna(), np.nan)
    return out


def check_missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Cuenta los vacíos por columna (solo las que tienen). No cambia los datos."""
    missing = df.isna().sum()
    report = pd.DataFrame({"missing": missing, "missing_pct": (missing / len(df) * 100).round(1)})
    return report[report["missing"] > 0].sort_values("missing", ascending=False)


def drop_sensitive_columns(df: pd.DataFrame, columns: tuple[str, ...] = EXCLUDE_FROM_FEATURES) -> pd.DataFrame:
    """Quita los atributos sensibles que no deben ser predictores (`gender`, `family_income`)."""
    return df.drop(columns=[c for c in columns if c in df.columns])


def extract_audit_columns(df: pd.DataFrame, columns: tuple[str, ...] = AUDIT_COLUMNS) -> pd.DataFrame:
    """Copia aparte (con el mismo índice) los atributos para auditar si el modelo falla más con algún grupo."""
    return df[[c for c in columns if c in df.columns]].copy()


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica en orden las decisiones del EDA y devuelve un DataFrame con **el mismo número de filas**.

    1. `student_id` al índice.  2. Crea el objetivo `pass_70` desde `exam_score` (corte en 70).
    3. Quita las 6 columnas de fuga (incluidas `exam_score` y `pass_status`).  4. Marca como vacío lo imposible.
    No quita los atributos sensibles: antes hay que guardar la copia de auditoría (ver el uso arriba).
    """
    out = drop_identifier(df)
    out = add_target(out)                    # primero el objetivo: después se quita exam_score
    out = drop_leakage_columns(out)
    out = mark_out_of_range(out)
    return out
