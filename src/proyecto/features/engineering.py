"""Variables del modelo y preprocesamiento (etapa 4).

Qué decide este archivo:
  * qué columnas entran al modelo (`feature_columns`): las 35 variables que dejó la etapa 3, sin las 6 columnas de
    fuga, sin `student_id`, `gender` ni `family_income`;
  * qué variables nuevas se prueban (`add_features`): cada una es una **hipótesis** que el notebook
    `04b_features_aprueba_o_no.ipynb` mide con los mismos pliegues y la misma métrica;
  * cómo se imputan los vacíos (`build_preprocessor`): **dentro del `Pipeline`**, ajustado solo con entrenamiento
    (mediana + indicador de vacío en las numéricas; categoría explícita «Desconocido» en las categóricas).

Ninguna función calcula medias ni medianas con todos los datos: eso lo hace el `Pipeline` en cada pliegue, con los
datos de entrenamiento de ese pliegue.
"""
from collections.abc import Iterable

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Variables que deja la etapa 3 (35 = 19 numéricas + 16 categóricas). Salen de `clean` + `drop_sensitive_columns`.
NUMERIC_BASE = (
    "age", "previous_exam_score", "previous_gpa", "attendance_percentage", "assignment_completion_rate",
    "study_hours_per_day", "self_study_hours", "private_tuition", "online_learning_hours",
    "practice_tests_completed", "sleep_hours", "daily_screen_time", "physical_activity_hours", "stress_level",
    "internet_access", "online_course_hours", "exam_preparation_days", "time_management_score",
    "exam_anxiety_level",
)
CATEGORICAL_BASE = (
    "education_level", "school_type", "parent_education", "urban_rural", "class_participation",
    "study_consistency", "study_environment", "study_method", "revision_frequency", "notes_quality",
    "sleep_quality", "break_frequency", "motivation_level", "device_availability", "educational_app_usage",
    "exam_difficulty",
)

# Dos datos del examen que aún no se sabe si existen al momento de avisar (decisión 7 del EDA): se miden «con y sin».
TIMING_COLUMNS = ("time_management_score", "exam_anxiety_level", "exam_difficulty")
# Siete variables numéricas con AUC ≈ 0,50 en el EDA (no separan a quien aprueba de quien pierde).
NO_SIGNAL_COLUMNS = (
    "age", "internet_access", "private_tuition", "daily_screen_time", "physical_activity_hours",
    "online_learning_hours", "online_course_hours",
)

# Propuesta de la etapa 4 (medida en `notebooks/04b_features_aprueba_o_no.ipynb`, pendiente de aprobación del grupo):
# quitar las 7 columnas sin señal y no agregar el indicador de vacío (en ambos casos el costo es el mismo, dentro del
# ruido, con menos columnas: la app pide 7 datos menos y `age`, que incluye menores, sale del modelo).
STAGE4_DROP = NO_SIGNAL_COLUMNS
STAGE4_ADD_MISSING_INDICATOR = False

# Variables nuevas que se pueden probar. Todas usan solo columnas de la MISMA fila (nada de otros estudiantes).
ENGINEERED_FEATURES = ("self_study_share", "prep_total_hours")

MISSING_CATEGORY = "Desconocido"


def _safe_ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    """División segura: denominador cero, negativo o vacío -> NaN (nunca infinito)."""
    return num / den.where(den > 0)


def add_features(df: pd.DataFrame, engineered: Iterable[str] = ENGINEERED_FEATURES) -> pd.DataFrame:
    """Añade las variables nuevas pedidas en `engineered`. No modifica el original.

    - `self_study_share` = `self_study_hours` / `study_hours_per_day`: qué parte de su estudio es autónomo.
      Se usa un cociente y no una suma porque `self_study_hours` ya es una parte de `study_hours_per_day`
      en el 100 % de las filas (decisión 6 del EDA).
    - `prep_total_hours` = `study_hours_per_day` × `exam_preparation_days`: horas totales de estudio antes del examen.
    """
    unknown = set(engineered) - set(ENGINEERED_FEATURES)
    if unknown:
        raise ValueError(f"Variables nuevas desconocidas: {sorted(unknown)}. Válidas: {list(ENGINEERED_FEATURES)}")
    out = df.copy()
    if "self_study_share" in engineered:
        out["self_study_share"] = _safe_ratio(out["self_study_hours"], out["study_hours_per_day"])
    if "prep_total_hours" in engineered:
        out["prep_total_hours"] = out["study_hours_per_day"] * out["exam_preparation_days"]
    return out


def feature_columns(drop: Iterable[str] = (), engineered: Iterable[str] = ()) -> tuple[list[str], list[str]]:
    """Devuelve (numéricas, categóricas) que usa el modelo.

    `drop` quita columnas de las 35 base (para medir «sin»); `engineered` añade variables nuevas a las numéricas.
    Un nombre mal escrito falla en voz alta en vez de ignorarse en silencio.
    """
    drop, engineered = set(drop), list(engineered)
    unknown_drop = drop - set(NUMERIC_BASE) - set(CATEGORICAL_BASE)
    if unknown_drop:
        raise ValueError(f"No puedo quitar columnas que no son variables base: {sorted(unknown_drop)}")
    unknown_new = set(engineered) - set(ENGINEERED_FEATURES)
    if unknown_new:
        raise ValueError(f"Variables nuevas desconocidas: {sorted(unknown_new)}")
    numeric = [c for c in NUMERIC_BASE if c not in drop] + engineered
    categorical = [c for c in CATEGORICAL_BASE if c not in drop]
    return numeric, categorical


def build_preprocessor(
    drop: Iterable[str] = (),
    engineered: Iterable[str] = (),
    add_missing_indicator: bool = True,
    scale: bool = False,
) -> ColumnTransformer:
    """Imputación (+ escalado opcional) de numéricas y one-hot de categóricas. Se ajusta solo con entrenamiento.

    - Numéricas: mediana del entrenamiento y, si `add_missing_indicator`, una columna 0/1 «estaba vacío».
    - Categóricas: los vacíos pasan a ser la categoría «Desconocido»; una categoría nunca vista se ignora (no falla).
    - `scale=True` solo hace falta para modelos lineales; los de árboles no lo necesitan.
    - Lo que no está en la lista (p. ej. una columna de fuga que alguien dejó en la tabla) se descarta (`remainder="drop"`).
    """
    numeric, categorical = feature_columns(drop, engineered)
    numeric_steps = [("impute", SimpleImputer(strategy="median", add_indicator=add_missing_indicator))]
    if scale:
        numeric_steps.append(("scale", StandardScaler()))
    categorical_steps = [
        ("impute", SimpleImputer(strategy="constant", fill_value=MISSING_CATEGORY)),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ]
    return ColumnTransformer(
        [("num", Pipeline(numeric_steps), numeric), ("cat", Pipeline(categorical_steps), categorical)],
        remainder="drop",
    )
