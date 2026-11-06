# Despliegue de la app

> Resultado de `notebooks/09b_inferencia_aprueba_o_no.ipynb` (plantilla del curso: `09_inferencia.ipynb`, sin modificar; ejemplo: `material-del-curso/ejemplo-creditsight/notebooks/09_inferencia.ipynb`).
> **Estado (2026-11-06):** la app **funciona en local** y su **paquete para Databricks Apps está armado y probado**, pero **todavía no está desplegada en Databricks**: falta hacerlo desde la interfaz web de Databricks (con la cuenta del usuario; **sin CLI**). **No hay enlace público.** Constancia: `reports/09_inferencia.json`.

## 1. Enlace y estado

| Dato | Valor |
|---|---|
| Enlace público de la app | **Pendiente** (se genera al desplegar en Databricks Apps) |
| Plataforma | **Databricks Apps** (aplicación tipo Streamlit alojada en el workspace). La app **no consulta** MLflow ni el registro: carga `models/model.joblib` de su propia carpeta |
| Código | `app/streamlit_app.py` (rama `feature/orendon`); paquete listo en `deploy/databricks_app/` (**se versiona** para que Databricks lo traiga con *Pull*; se regenera con `python scripts/prepare_databricks_app.py`) |
| Versión de Python | ☑ 3.12 con la que se entrenó; ☑ **3.11 en Databricks Apps** (comprobado: la app del paquete corre con Python 3.11 y da los mismos resultados). `numpy` va con rango (`>=2.3,<2.5`) porque 2.5.x exige 3.12; las demás versiones están fijadas |
| ¿Se comprobó en una ventana privada? | ☐ no aplica todavía (no hay enlace) |
| ¿Se desplegó? | ☐ sí  ☑ no → **plan B** (apartado 4) |

## 2. Decisiones de despliegue y su motivo

| Decisión | Motivo |
|---|---|
| La app carga `models/model.joblib` y `models/input_schema.json` desde su carpeta y **no consulta Databricks ni MLflow** | Regla 8 del proyecto: sin credenciales dentro de la app y sin depender de la cuota de una plataforma. Hospedarla en Databricks Apps no cambia eso: solo es dónde corre |
| `model.joblib` se exporta del **registro** (`estudiantes_aprueba_o_no@champion`), no del archivo de la etapa 7 | Garantiza que se entrega lo que quedó registrado; el notebook comprueba que da **las mismas probabilidades** que la prueba de la etapa 7 (diferencia 0,0) |
| Rangos **posibles** por columna (p. ej. horas de estudio 0–24, nota 0–100, promedio 1–4) distintos de los observados | Un dato imposible hace que la app **se niegue** a responder y explique qué corregir; un dato raro pero posible solo avisa. En el formulario los límites ya son los posibles |
| Perfiles de ejemplo con estudiantes **reales del entrenamiento** (riesgo alto, intermedio y bajo) | Quien abre la app empieza desde algo razonable; no se usa la prueba |
| La decisión es «avisar si P(`Fail`) ≥ 1/6» (matriz de costos 5 : 1) y se marca «revisar» cuando la decisión difiere de la clase más probable o el modelo duda | Es la misma regla congelada en la etapa 7 (comprobado en 2.000 estudiantes); marcar «revisar» recuerda que es una alerta para revisión humana |
| Paquete mínimo (`scripts/prepare_databricks_app.py`): app, `inference/`, modelo, esquema, ficha, `app.yaml` y `requirements.txt` con solo 5 paquetes | El modelo es un `Pipeline` de scikit-learn y no necesita nada más de `src/`; así el paquete pesa 0,04 MB y no arrastra datos ni credenciales |
| Qué NO se sube | `.env`, tokens, `data/` (el CSV y los `train/test`), `mlflow_local.db`, `models/final_pipeline.joblib` y los notebooks |

## 3. Pruebas

### Pruebas de la app en local (hechas, `AppTest` de Streamlit sobre la app real)

| Caso | Datos usados | Resultado esperado | Resultado real |
|---|---|---|---|
| Normal, riesgo alto | Perfil de ejemplo con P(`Fail`) > 90 % (estudiante real del entrenamiento) | Alerta | **ALERTA**, P(`Fail`) 93,8 %, «el modelo está seguro»; igual a la predicción directa |
| Límite (cambia la decisión) | Perfil intermedio (P entre 40 % y 60 %) | Alerta con «revisión recomendada» (la clase más probable es `Pass`, pero P(`Fail`) > 1/6) | **ALERTA**, P(`Fail`) 46,9 %, revisión recomendada; igual a la directa |
| Normal, riesgo bajo | Perfil con P(`Fail`) < 5 % | Sin alerta | **Sin alerta**, P(`Fail`) 4,7 %; igual a la directa |
| Con un campo en «No sé» | Perfil intermedio con la nota previa en «No sé» | Responde (el `Pipeline` imputa) | Responde: alerta, 46,9 %, sin errores |
| Inválido (debe rechazarse) | `study_hours_per_day` = 30; `previous_exam_score` = 250; `previous_gpa` = 7 (probado en la función de predicción; el formulario ya impide escribirlos) | Se niega con un mensaje claro | «debe estar entre 0 y 24», «entre 0 y 100», «entre 1 y 4» |

Además: el formulario muestra los 12 campos numéricos, las 16 listas y las 12 casillas «No sé»; la app del **paquete** corre sola en un proceso aparte, sin `src/` ni el repositorio, y da el mismo resultado (alerta, 93,8 %). Pruebas automáticas: **133** en `tests/` (9 nuevas: esquema con ejemplos y paquete de Databricks).

### Pruebas del enlace público

**Pendientes**: no hay enlace. Cuando exista, repetir los cinco casos de arriba en una ventana privada y anotar aquí el resultado.

## 4. Problemas encontrados y plan B

- **Encontrados y resueltos:** (1) Streamlit avisaba de que un campo tenía valor por defecto y también valor puesto por el perfil de ejemplo → ahora no se pasa el valor por defecto cuando el perfil ya lo fijó; (2) un booleano de NumPy no se podía guardar en JSON → se convirtió; (3) el notebook 09 de la plantilla era un esqueleto sin configurar → se creó el `09b` completo.
- **Error en el primer despliegue (2026-11-06 11:44):** el *build* de Databricks Apps falló al instalar `requirements.txt` con «Ignored the following versions that require a different python version: … 2.5.4 Requires-Python >=3.12». **Causa:** Databricks Apps usa Python 3.11 y el proyecto usa 3.12; `numpy==2.5.4` exige 3.12 o más. **Arreglo:** en el paquete `numpy` pasa a `numpy>=2.3,<2.5` (resuelve a 2.4.x); `pandas==3.0.6`, `scikit-learn==1.9.1`, `streamlit==1.66.0` y `joblib==1.6.0` se mantienen (comprobado). **Comprobación:** se creó un entorno con Python 3.11, se instaló el `requirements.txt` nuevo y se ejecutó la app del paquete: mismos resultados (alto 93,8 %, intermedio 46,9 %, bajo 4,7 %). Está en `scripts/prepare_databricks_app.py` (`REQUIREMENT_OVERRIDES`) y tiene prueba. **Para aplicarlo:** `git push`, *Pull* en el Git folder y *Deploy* otra vez.
- **No resuelto, depende de la cuenta de Databricks:** el despliegue. Se probó todo lo que no lo necesita.
- **Plan B** (si la app falla en vivo): capturas de la app en local (`img` del Word y de la presentación, tomadas con Edge el 2026-11-06) y `streamlit run app/streamlit_app.py` en el equipo del grupo.
- **Plan de despliegue escrito (sin CLI: `git push`, *Pull* en Databricks y despliegue desde la interfaz):**

  **A. En tu equipo (una vez):**
  1. `python scripts/prepare_databricks_app.py` (regenera `deploy/databricks_app/`; ya está hecho y el notebook 09b lo comprueba).
  2. Subir al repositorio **solo lo necesario** (no hace falta subir `mlflow_local.db`):
     `git add deploy/databricks_app app/streamlit_app.py src/proyecto/inference scripts/prepare_databricks_app.py models/model.joblib models/input_schema.json notebooks/09b_inferencia_aprueba_o_no.ipynb reports tests .gitignore` → `git commit -m "app lista para Databricks Apps"` → `git push origin feature/orendon`.

  **B. En Databricks (interfaz web):**
  1. **Conectar GitHub** (una vez): *Settings → Linked accounts* (o *User settings → Git integration*) → GitHub → pegar un *Personal Access Token* con permiso de lectura al repositorio. Si el repo es privado es obligatorio.
  2. **Traer el repo:** menú *Workspace* → *Create → Git folder* → URL `https://github.com/123omarrendon/esp_lab_analisis_avanzado.git` → *Create*. Dentro de la carpeta, elegir la rama `feature/orendon` (selector de rama arriba) y pulsar *Pull*. Comprobar que existe `deploy/databricks_app/` con `app.yaml`, `requirements.txt`, `app/`, `src/` y `models/`.
  3. **Crear la app:** menú *Compute* → pestaña *Apps* → *Create app* → elegir **Custom** (aplicación personalizada), nombre `estudiantes-aprueba-o-no`, sin recursos adicionales (no necesita bodega SQL ni modelo servido) → *Create*.
  4. **Desplegar:** en la app, *Deploy* → *Browse* y elegir la carpeta del Git folder `.../deploy/databricks_app` (la que tiene `app.yaml`) → *Deploy*. Esperar a que el estado pase a *Running* (la primera vez instala las librerías de `requirements.txt`).
  5. **Probar:** abrir la **URL** de la app (arriba, junto al estado), en una ventana privada; repetir los cinco casos del apartado 3 y anotar aquí el resultado real. Si falla, abrir la pestaña de **Logs** de la app.
  6. **Actualizar después de un cambio:** `git push` → en el Git folder *Pull* → en la app *Deploy* otra vez con la misma carpeta.

  **Notas y riesgos:** los nombres exactos de menús y botones cambian con las versiones de Databricks (esta guía es del 2026-11-06); si algo no coincide, buscar «Apps» o «Git folder» en la barra de búsqueda del workspace. Las versiones de `requirements.txt` deben existir para el Python del workspace; si la instalación falla, el log lo dice y se ajustan en `deploy/databricks_app/requirements.txt` (cuidando que `scikit-learn` sea la misma con la que se guardó el modelo, 1.9.1). El Git folder trae también datos y notebooks del repo; la app solo usa la subcarpeta indicada.
- **Antes de desplegar**, confirmar con la institución los supuestos de la ficha: costos 5 : 1, capacidad de tutoría y que `exam_difficulty` se conoce al avisar.

## 5. Ensayo cronometrado (clase 5)

| Parte | Tiempo previsto | Tiempo real |
|---|---|---|
| Caso de negocio | 2 min | |
| App (demo en vivo) | 4 min | |
| Resultados | 3 min | |
| Cierre | 1 min | |
