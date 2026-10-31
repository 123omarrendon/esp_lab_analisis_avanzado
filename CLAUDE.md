# Instrucciones permanentes para Claude (proyecto del curso)

Este archivo lo lees al inicio de cada conversación. Sigue estas reglas siempre.

## Quién soy y qué hacemos

- Soy estudiante de la Maestría en Ingeniería Analítica. **Soy analista, no desarrollador.**
  Explica lo que haces, con palabras simples, antes y después de cambiar código.
- Trabajo en un grupo. Estamos construyendo un proyecto de machine learning de principio a fin,
  como si fuera una startup: caso de negocio, EDA, preprocesamiento, features, torneo de modelos,
  optimización, validación, tracking en Databricks, app en Streamlit, reporte y presentación.
- El caso, el dataset, la métrica y el tipo de problema están en `especificacion-proyecto.md`.
  **Léelo antes de generar código** y avísame si algo del pedido lo contradice.
- Cada etapa tiene su especificación en `especificaciones/` (`02-eda.md`, `03-preprocesamiento.md`…). Si la
  de la etapa en curso tiene secciones vacías, **pídeme que las llene antes de escribir código**. Una vez llena,
  implementa exactamente lo que dice (reglas, umbrales, forma de partir, pruebas) y avísame si algo no se puede.
- Los principios del proyecto están en `.specify/memory/constitution.md`: **léela** y avísame si un pedido la contradice.
- Trabajamos con Spec Kit: especificación → plan → tareas → código. **No escribas código de una pieza nueva sin que yo
  haya leído y aprobado su `plan.md` y su `tasks.md`.** Marca cada tarea de `tasks.md` como hecha solo cuando su prueba pasa.
- Para revisar uso los subagentes de `.claude/agents/` (`auditor-de-fuga`, `escritor-de-pruebas`, `revisor-de-codigo-ia`);
  sus informes no reemplazan que yo entienda el código.

## Datos del proyecto (resumen; el detalle está en `data/README.md`)

- **Archivo:** `data/student_exam_performance.csv` (100.000 filas × 44 columnas; una fila = un estudiante, `student_id` único).
- **Regla de aprobación:** el estudiante **aprueba con 70 o más** y **pierde el curso con menos de 70** (69 y 69,99 pierden; 70 aprueba).
- **Objetivo:** `pass_70` (`Pass` 30,8 % / `Fail` 69,2 %), derivado de `exam_score` con `add_target` (`src/proyecto/data/cleaning.py`); clasificación binaria, clase de interés `Fail`. **No uses `pass_status`** como objetivo: el dataset lo calcula con corte en 50.
- **Métricas:** costo esperado por estudiante (falso negativo : falso positivo = 5 : 1, supuesto), *recall* de `Fail` y NPV. La estrategia sin modelo a vencer es «avisar a todos» (costo 0,31); un modelo la supera solo con NPV > 83,3 %. La exactitud y el *recall* solos no sirven.
- **Nunca uses como entrada:** `exam_score`, `pass_status` (corte 50), `performance_grade`, `performance_level`, `questions_correct`, `questions_attempted` (derivan de la nota o son datos del examen), `student_id`, `gender` y `family_income`. El objetivo se crea **antes** de quitar `exam_score`.
- **Con y sin (etapa 4):** `time_management_score`, `exam_anxiety_level`, `exam_difficulty`. Medido en `notebooks/04b_features_aprueba_o_no.ipynb`: `exam_difficulty` pesa mucho (sin ella el costo sube de 0,258 a 0,283) y es un supuesto de negocio (¿se conoce al avisar?); las otras dos no aportan si ella está.
- **Variables (etapa 4, propuesta):** 28 = las 35 de la etapa 3 menos 7 sin señal (`age`, `internet_access`, `private_tuition`, `daily_screen_time`, `physical_activity_hours`, `online_learning_hours`, `online_course_hours`); sin indicador de vacío; ninguna variable nueva mejoró (`self_study_share`, `prep_total_hours`). Código en `src/proyecto/features/engineering.py`; pliegues: `make_folds` (5, por fila, estratificados, semilla 42).
- **Torneo (etapa 5, propuesta):** `notebooks/05b_torneo_aprueba_o_no.ipynb`; candidatos en `candidates()` (`src/proyecto/models/train.py`). Regresión logística, LightGBM y XGBoost empatan (costo ≈ 0,258); random forest es peor (0,283). Finalistas propuestos: **regresión logística y LightGBM**. Con costo 5 : 1 el modelo avisa a ≈ 90 de cada 100 (especificidad 0,30): la capacidad de tutoría la define la institución.
- **Partición:** por fila, estratificada por `pass_70` (no hay entidades repetidas), 80/20, semilla 42 (`split_train_test`).
- **Vacíos** en 7 columnas (`attendance_percentage`, `time_management_score`, `notes_quality`, `previous_gpa`, `sleep_quality`, `parent_education`, `device_availability`): no se borran filas; se resuelven dentro del `Pipeline`.
- **Sensibles:** `age` (incluye menores), `gender`, `family_income`, `parent_education`, `urban_rural`, `school_type`: audita el desempeño por grupo.

## Estructura obligatoria del repositorio

```text
README.md  CLAUDE.md  especificacion-proyecto.md  especificaciones/  requirements.txt  .env.example  .gitignore
.specify/        # Spec Kit: constitución (memory/constitution.md), plantillas y scripts
.claude/         # skills de Spec Kit (/speckit-…) y subagentes (agents/)
specs/           # lo que genera Spec Kit por pieza de trabajo: spec.md, plan.md, tasks.md
data/raw/        # datos originales: NUNCA se modifican
data/processed/
notebooks/       # numerados por etapa; solo orquestan, sin lógica reutilizable
src/proyecto/    # data/ features/ models/ tracking/ inference/
tests/           # pytest
models/          # model.joblib + ficha_modelo.md
app/streamlit_app.py
reports/         # una sección por hito + informe_tecnico.md
presentacion/    # ejecutiva.md (máximo 5 diapositivas)
scripts/
```

- La lógica reutilizable va en `src/`; los notebooks importan de `src/`, nunca al revés.
- `requirements.txt` está en la raíz, con versiones fijadas y Python 3.12.

## Estilo

- **Textos, comentarios y documentación en español. Nombres de variables, funciones y archivos de
  código en inglés** (`clean_income`, no `limpiar_ingreso`).
- Cambios pequeños: una cosa por vez, en el archivo que te indico. No reescribas el proyecto entero.
- Si no estás seguro, pregunta antes de inventar.

## Reglas que no se negocian

1. **No inventes datos.** Si una columna, un valor o un resultado no existe, dilo. Nunca
   fabriques métricas ni resultados.
2. **No subas secretos ni datos personales.** `.env` está en `.gitignore`; no imprimas ni
   escribas tokens. Elimina o anonimiza nombres, documentos de identidad y similares.
3. **Parte los datos por la unidad correcta.** Si un mismo cliente, paciente o empresa aparece en
   varias filas, la partición entrenamiento/validación/prueba y la validación cruzada se hacen
   **por grupo** (`GroupKFold`, `StratifiedGroupKFold`, `GroupShuffleSplit`), no por fila.
4. **No uses el conjunto de prueba para decidir nada.** Se abre una sola vez, al final, en la
   etapa de validación. Elegir modelo, umbral o hiperparámetros se hace con validación.
5. **Todo preprocesamiento va dentro de un `Pipeline`** ajustado solo con entrenamiento, para
   evitar fuga de información.
6. **Cada decisión de datos se escribe con su motivo** en `reports/`, no solo en el código.
7. **El seguimiento de experimentos usa MLflow en Databricks.** Lee la conexión desde `.env`
   (`PROFILE` o `DATABRICKS_HOST` y `DATABRICKS_TOKEN`). Define `PYTHONUTF8=1` en Windows.
8. **La app NO consulta Databricks.** Carga `models/model.joblib` desde el repositorio. Valida
   las entradas del formulario y muestra un aviso de uso responsable.
9. **Pruebas.** Cada función de `src/` que limpia datos o transforma variables debe tener una
   prueba en `tests/`. Ejecútalas con `pytest` antes de darme el cambio por terminado.

## Cómo quiero que respondas

1. Resume en 2–3 frases qué vas a hacer y por qué.
2. Haz el cambio.
3. Dime cómo comprobar que funciona (el comando exacto) y qué resultado debería ver.
4. Si hay un riesgo (fuga de información, datos personales, métrica engañosa), avísame.
