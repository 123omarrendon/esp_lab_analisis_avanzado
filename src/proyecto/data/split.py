"""Partición entrenamiento / prueba (etapa 3).

`student_id` es único (100.000 ids para 100.000 filas): ningún estudiante se repite, así que se parte **por fila**,
**estratificada por `pass_70`** (aprueba con 70 o más) para mantener el ~69,2 % de `Fail` en los dos lados.
Si algún día un estudiante apareciera en varias filas, esta función NO sirve: habría que partir por grupo.
"""
import pandas as pd
from sklearn.model_selection import train_test_split

from proyecto.data.cleaning import TARGET


def split_train_test(
    df: pd.DataFrame, target: str = TARGET, test_size: float = 0.2, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parte en entrenamiento y prueba, estratificado por el objetivo. Conserva el índice (`student_id`).

    La prueba se guarda cerrada: no se mira hasta la validación final (etapa 7).
    """
    if target not in df.columns:
        raise KeyError(f"Falta la columna objetivo '{target}'.")
    if df.index.duplicated().any():
        raise ValueError("El índice tiene valores repetidos: partir por fila podría separar a un mismo estudiante.")
    train, test = train_test_split(df, test_size=test_size, random_state=seed, stratify=df[target])
    return train, test
