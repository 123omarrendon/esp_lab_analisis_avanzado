"""Tabla de juguete compartida por las pruebas de la etapa 4 (pytest agrega tests/ al path, por eso `from toy import ...`)."""
import numpy as np
import pandas as pd

from proyecto.features.engineering import CATEGORICAL_BASE, NUMERIC_BASE


def make_students(n: int = 40) -> pd.DataFrame:
    """Tabla de juguete con las 35 variables de la etapa 3, algunos vacíos y números sencillos."""
    rng = np.random.default_rng(0)
    df = pd.DataFrame({c: rng.integers(1, 10, n).astype(float) for c in NUMERIC_BASE})
    for c in CATEGORICAL_BASE:
        df[c] = np.where(np.arange(n) % 2 == 0, "A", "B")
    df["self_study_hours"] = 2.0
    df["study_hours_per_day"] = 4.0
    df["exam_preparation_days"] = 5.0
    df.loc[0, "previous_gpa"] = np.nan          # vacío numérico
    df.loc[1, "parent_education"] = np.nan       # vacío categórico
    return df
