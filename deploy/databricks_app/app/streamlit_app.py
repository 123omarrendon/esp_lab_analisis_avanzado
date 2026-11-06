"""App del proyecto: alerta de posible pérdida del curso (pass_70). El formulario se construye solo a partir de
`models/input_schema.json`.

- Carga `models/model.joblib` desde ESTE repositorio (o desde la carpeta de la app en Databricks Apps). NO consulta
  MLflow ni el registro de Databricks: no hay credenciales en la app, y no depende de la cuota de ninguna plataforma.
- Valida las entradas: si un dato es imposible, explica qué corregir en vez de responder cualquier cosa.
- Ofrece perfiles de ejemplo (filas reales del entrenamiento) para empezar el formulario desde algo razonable.

Ejecutar en local (desde la raíz del repo):  streamlit run app/streamlit_app.py
En Databricks Apps: el paquete que arma `scripts/prepare_databricks_app.py` mantiene este mismo diseño de carpetas
(app/, src/, models/) y su `app.yaml` lanza este archivo; ver `reports/09_despliegue.md`.

Para personalizarla (título, etiquetas, ejemplos, aviso de uso responsable) edita `models/input_schema.json`
(claves `app_title`, `labels`, `examples`, `decision_labels`, `focus_class`, `responsible_use`) o este archivo.
"""
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "model.joblib"
SCHEMA_PATH = ROOT / "models" / "input_schema.json"
UNKNOWN = "(no sé)"

# El paquete de src/ puede llamarse `proyecto` o el nombre que le hayas puesto: lo buscamos.
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
PACKAGE = next((p.name for p in sorted(SRC.iterdir()) if p.is_dir() and (p / "__init__.py").exists()), "proyecto")
predict_module = importlib.import_module(f"{PACKAGE}.inference.predict")
schema_module = importlib.import_module(f"{PACKAGE}.inference.schema")

DEFAULT_RESPONSIBLE_USE = (
    "- Esta herramienta **apoya** una decisión; la decisión final es de una persona.\n"
    "- Fue entrenada con los datos de este proyecto: no la uses fuera de ese contexto sin validarla de nuevo.\n"
    "- Revisa los **límites del modelo** en `models/ficha_modelo.md` antes de usarla."
)


@st.cache_resource
def get_model():
    return predict_module.load_model(MODEL_PATH)


@st.cache_data
def get_schema() -> dict:
    return schema_module.load_schema(SCHEMA_PATH)


def label(schema: dict, column: str) -> str:
    return schema.get("labels", {}).get(column, column)


NO_EXAMPLE = "(formulario vacío)"


def apply_example() -> None:
    """Rellena el formulario con el perfil de ejemplo elegido (se ejecuta al cambiar el selector)."""
    schema = get_schema()
    name = st.session_state.get("example_choice", NO_EXAMPLE)
    example = schema.get("examples", {}).get(name)
    if not example:
        return
    for column in schema["numeric"]:
        low, high = schema.get("valid_range", {}).get(column) or schema["observed_range"][column]
        value = min(max(float(example[column]), low), high)
        st.session_state[f"unk_num_{column}"] = False
        st.session_state[f"num_{column}"] = int(round(value)) if column in schema.get("integer_columns", []) else value
    for column in schema["categorical"]:
        st.session_state[f"cat_{column}"] = str(example[column])


def numeric_field(schema: dict, column: str, key: str):
    """Un campo numérico con su rango y mediana, y una casilla 'no sé' que deja el dato vacío."""
    low, high = schema.get("valid_range", {}).get(column) or schema["observed_range"][column]
    default = float(schema["median"][column])
    is_int = column in schema.get("integer_columns", [])
    if high <= low:
        high = low + 1
    default = min(max(default, low), high)
    unknown = st.checkbox(f"No sé: {label(schema, column)}", key=f"unk_{key}")
    if unknown:
        return np.nan
    # Si un perfil de ejemplo ya fijó el valor en session_state, no se pasa `value` (Streamlit avisa si van los dos).
    start = {} if key in st.session_state else {"value": int(round(default)) if is_int else float(default)}
    if is_int:
        return st.number_input(label(schema, column), min_value=int(low), max_value=int(high), step=1, key=key, **start)
    return st.number_input(label(schema, column), min_value=float(low), max_value=float(high), key=key, **start)


def build_form(schema: dict) -> dict:
    """Dibuja el formulario (tres columnas) y devuelve una fila de entrada."""
    row = {}
    columns = schema["numeric"] + schema["categorical"]
    cols = st.columns(3)
    for i, column in enumerate(columns):
        with cols[i % 3]:
            if column in schema["categorical"]:
                options = schema["categories"][column] + [UNKNOWN]
                choice = st.selectbox(label(schema, column), options, key=f"cat_{column}")
                row[column] = np.nan if choice == UNKNOWN else choice
            else:
                row[column] = numeric_field(schema, column, f"num_{column}")
    return row


def main() -> None:
    st.set_page_config(page_title="Alerta de pérdida del curso", page_icon="🎓", layout="wide")

    if not MODEL_PATH.exists() or not SCHEMA_PATH.exists():
        st.title("Alerta de pérdida del curso")
        st.error(
            "Falta `models/model.joblib` o `models/input_schema.json`. "
            "Ejecuta el notebook `notebooks/09b_inferencia_aprueba_o_no.ipynb` para generarlos."
        )
        st.stop()

    model, schema = get_model(), get_schema()
    st.title(schema.get("app_title", "Alerta de pérdida del curso"))
    st.caption("Herramienta de apoyo a la decisión. **No decide por sí sola.**")

    if schema.get("examples"):
        st.selectbox("Empezar desde un perfil de ejemplo (estudiantes reales del entrenamiento)",
                     [NO_EXAMPLE] + list(schema["examples"]), key="example_choice", on_change=apply_example)

    with st.form("entrada"):
        row = build_form(schema)
        submitted = st.form_submit_button("Evaluar", type="primary")

    if not submitted:
        st.info("Completa los datos y pulsa **Evaluar**. Marca *No sé* en lo que no conozcas.")
        return

    try:
        result = predict_module.predict_with_scores(pd.DataFrame([row]), model, schema)
    except predict_module.InputValidationError as error:
        st.error(f"Revisa los datos: {error}")
        return

    first = result.iloc[0]
    class_names = schema["class_names"]
    left, right = st.columns(2)
    with left:
        decision = str(first["decision"])
        st.metric("Resultado sugerido", schema.get("decision_labels", {}).get(decision, decision))
        focus = schema.get("focus_class")
        if focus:
            st.metric(f"Probabilidad de {focus}", f"{first[f'proba_{focus}']:.1%}".replace(".", ","))
        detail = f"Clase más probable: **{first['most_likely']}**"
        if "expected_cost" in result.columns:
            detail += f" · costo esperado de esta decisión: **{first['expected_cost']:.2f}**"
        st.caption(detail)
        if bool(first["needs_review"]):
            st.warning("**Revisión recomendada:** el modelo duda, o la decisión de menor costo difiere de la clase más probable.")
        else:
            st.success("El modelo está seguro de este resultado.")
        for message in result.attrs.get("warnings", []):
            st.warning(message)
    with right:
        st.write("**Probabilidad por clase**")
        st.bar_chart(pd.DataFrame({"probabilidad": [first[f"proba_{c}"] for c in class_names]}, index=class_names))

    if "cost_matrix" in schema:
        with st.expander("¿Cómo se decide? (matriz de costos)"):
            st.markdown("La decisión es la de **menor costo esperado**, no necesariamente la más probable.")
            st.dataframe(pd.DataFrame(schema["cost_matrix"], index=[f"real {c}" for c in class_names], columns=[f"decide {c}" for c in class_names]))
    with st.expander("Uso responsable"):
        st.markdown(schema.get("responsible_use", DEFAULT_RESPONSIBLE_USE))


if __name__ == "__main__":  # `streamlit run` ejecuta el archivo como programa principal
    main()
