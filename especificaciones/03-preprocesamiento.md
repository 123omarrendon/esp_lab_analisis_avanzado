# Especificación · Etapa 3 · Preprocesamiento (limpieza y partición)

> Se llena **antes** de pedirle código a Claude, a partir de la tabla de decisiones de
> `especificaciones/02-eda.md`. Claude la lee y la implementa; ustedes revisan que el código haga
> **exactamente** esto (`material-del-curso/kit/checklist-revision-ia.md`).
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`, sección 4 · Ejemplo: `material-del-curso/ejemplo-creditsight/src/creditsight/data/`.
> Variables y cifras del dataset: `data/README.md`.

**Grupo:** _______________   **Fecha:** 2026-10-31   **Estado:** ☑ borrador  ☐ cerrada

> **Regla del caso:** el estudiante **aprueba con 70 o más** y **pierde el curso con menos de 70** (69 y 69,99 pierden; 70 aprueba). El objetivo es **`pass_70`**, derivado de `exam_score`.
> La columna `pass_status` del dataset usa el corte en 50: no es el objetivo y se excluye como fuga. Implementado y probado en `src/proyecto/data/` y `tests/`; orquestado por `notebooks/03b_preprocesamiento_aprueba_o_no.ipynb`.

## 1. Unidad de análisis y partición

- **Una fila es:** un estudiante con sus hábitos de estudio, su contexto y el resultado de un examen.
- **Entidad que se repite (columna):** `student_id`  ☑ no se repite → partir por fila es válido porque: hay 100.000 ids distintos para 100.000 filas, así que un mismo estudiante nunca cae en entrenamiento y prueba a la vez.
- **Se parte por:** ☐ grupo (`GroupShuffleSplit` / `StratifiedGroupKFold`) ☑ fila, **estratificada por `pass_70`** (`train_test_split(..., stratify=y)`; en validación cruzada, `StratifiedKFold`)
- **Proporción de prueba:** 20 %   **Semilla:** 42
- **¿Hay orden temporal que respetar?** ☑ no → el dataset no tiene fechas ni periodo
- **Dónde se guarda la prueba:** `data/processed/` (cerrada: **no se mira** hasta la etapa 7)
- **Resultado esperado de la partición:** 80.000 filas de entrenamiento y 20.000 de prueba, con ≈ 69,2 % de `Fail` (nota < 70) en cada una.

## 2. Datos personales

| Columna | Qué es | Se elimina en | Prueba que lo verifica |
|---|---|---|---|
| `student_id` | Identificador seudonimizado (`STU_000001`…); no explica el resultado | `load_raw()` (primer paso al cargar; queda solo como índice) | `test_no_personal_columns` |
| `gender` | Atributo sensible; no entra como predictor | `drop_sensitive_columns()`; antes, `extract_audit_columns()` lo guarda aparte solo para auditar la equidad | `test_no_personal_columns` |
| `family_income` | Atributo sensible con brecha de 15 puntos en `Fail` (75,5 % con ingreso bajo vs 60,5 % con alto; EDA, decisión 8); no entra como predictor por defecto | `drop_sensitive_columns()`; igual que `gender`, queda en la tabla de auditoría | `test_no_personal_columns` |

> `age`, `family_income`, `parent_education`, `urban_rural` y `school_type` también son demográficas, pero se **conservan** como candidatas (ver `data/README.md`). Decisión del grupo: si alguna se descarta, agregarla a esta tabla.

## 3. Reglas de limpieza

Una fila por decisión del EDA. **Una función, una prueba.** Se marca como vacío lo imposible; no se borran filas sin criterio.

| # (de la tabla del EDA) | Columna(s) | Problema | Regla exacta (con el umbral o valor) | Función en `src/proyecto/data/cleaning.py` | Prueba en `tests/test_cleaning.py` |
|---|---|---|---|---|---|
| 1a | `exam_score` | El objetivo se deriva de la nota | Crear `pass_70`: `Pass` si la nota es **≥ 70**, `Fail` si es **< 70** (69 y 69,99 pierden; 70 aprueba). Se crea **antes** de quitar `exam_score`; falla si falta la nota o hay notas vacías | `add_target` | `test_add_target_applies_the_70_rule_on_a_normal_case`, `test_add_target_boundary_69_fails_and_70_passes`, `test_add_target_is_not_the_dataset_pass_status` |
| 1b | `exam_score`, `pass_status` (corte 50), `performance_grade`, `performance_level`, `questions_correct`, `questions_attempted` | Fuga: contienen la respuesta o se conocen al rendir el examen | Quitar estas **6** columnas de las variables de entrada; `pass_70` se conserva como objetivo | `drop_leakage_columns` | `test_drop_leakage_columns_removes_the_six_and_keeps_target` |
| 2 | `parent_education`, `previous_gpa`, `attendance_percentage`, `notes_quality`, `sleep_quality`, `device_availability`, `time_management_score` | Vacíos (3,0 % a 9,9 %) | No borrar filas; el resultado es un informe con el número de vacíos por columna | `check_missing_report` | `test_check_missing_report` |
| 3 | `student_id` | Identificador | Pasarlo a índice y quitarlo de las variables de entrada; si hay `student_id` repetidos, fallar con error | `drop_identifier` | `test_drop_identifier` |
| 4 | `pass_70` | Se debe mantener la proporción de `Fail` (69,2 %) en los dos lados | Partir 80/20 con `stratify=pass_70` y semilla 42 | `split_train_test` (en `split.py`) | `test_split.py` (ver sección 6) |
| 5 | `previous_exam_score`, `previous_gpa`, `attendance_percentage`, `assignment_completion_rate`, `sleep_hours`, `study_hours_per_day`, `online_learning_hours` | Valores imposibles | Volver vacío: notas y porcentajes fuera de 0–100, `previous_gpa` fuera de 1–4, `sleep_hours`, `study_hours_per_day`, `self_study_hours` y `online_learning_hours` fuera de 0–24. **No** recortar extremos plausibles (12 h de estudio, 15 h en línea) | `mark_out_of_range` | `test_mark_out_of_range` |
| 6 | `gender`, `family_income` | Atributos sensibles | Separarlos de las variables de entrada y guardar aparte (con `urban_rural`, `school_type`, `education_level`, `age`) para auditar equidad | `drop_sensitive_columns` y `extract_audit_columns` | `test_drop_sensitive_columns_removes_gender_and_family_income`, `test_extract_audit_columns_keeps_the_same_index`, `test_no_personal_columns_in_the_features` |

## 4. Vacíos

| Columna | Qué significa el vacío | Tratamiento hoy | Tratamiento en la etapa 4 (dentro del `Pipeline`) |
|---|---|---|---|
| `parent_education` (6,5 %) | ☑ no se anotó | ☑ dejar vacío | Categoría explícita "Desconocido" |
| `previous_gpa` (7,8 %) | ☑ no se anotó | ☑ dejar vacío | Imputar con la mediana del entrenamiento y agregar indicador de vacío |
| `attendance_percentage` (9,9 %) | ☑ no se anotó | ☑ dejar vacío | Imputar con la mediana del entrenamiento y agregar indicador de vacío |
| `notes_quality` (8,4 %) | ☑ no se anotó | ☑ dejar vacío | Categoría explícita "Desconocido" |
| `sleep_quality` (7,0 %) | ☑ no se anotó | ☑ dejar vacío | Categoría explícita "Desconocido" |
| `device_availability` (3,0 %) | ☑ no se anotó | ☑ dejar vacío | Categoría explícita "Desconocido" |
| `time_management_score` (9,6 %) | ☑ no se anotó | ☑ dejar vacío | Imputar con la mediana del entrenamiento y agregar indicador de vacío |

> Imputar con medias o medianas **no se hace aquí**: depende del entrenamiento y va dentro del `Pipeline`.
> El significado "no se anotó" es una lectura de Claude: no se vio relación entre el vacío y el resultado (`Fail` 68,3–69,4 % con vacío frente a ≈ 69,2 % sin vacío). El grupo debe confirmarlo.

## 5. Entradas y salidas

| | Ruta |
|---|---|
| Entrada | `data/student_exam_performance.csv` (nunca se modifica; la estructura del curso pide `data/raw/`: decidir si se mueve) |
| Salida: entrenamiento | `data/processed/train.joblib` (35 variables + `pass_70`, índice `student_id`) |
| Salida: prueba (cerrada) | `data/processed/test.joblib` |
| Salida: auditoría de equidad | `data/processed/audit_train.joblib` y `audit_test.joblib` (mismos estudiantes, sin entrar al modelo) |
| Nota | `data/processed/` está en `.gitignore`: se regenera con el notebook `03b_preprocesamiento_aprueba_o_no.ipynb` |
| Código de limpieza | `src/proyecto/data/cleaning.py` |
| Código de partición | `src/proyecto/data/split.py` |
| Notebook que orquesta | `notebooks/03b_preprocesamiento_aprueba_o_no.ipynb` (solo llama a las funciones; la plantilla del curso es `03_preprocesamiento.ipynb`) |

## 6. Pruebas que deben existir

- ☐ **Partición:** ninguna entidad aparece en dos particiones y no se pierde ninguna fila (`tests/test_split.py`); además, la proporción de `Fail` es ≈ igual (69,2 %) en entrenamiento y prueba.
- ☐ **La prueba de partición falla** si se cambia temporalmente a una partición sin estratificar o a una que repita `student_id` (compruébenlo y vuelvan a dejarla bien).
- ☐ **Una prueba por regla de limpieza** de la sección 3, con un caso normal y un caso sucio hechos a mano.
- ☐ **Datos personales:** el resultado de cargar no contiene `student_id` ni `gender` entre las variables de entrada.
- ☐ **Fuga:** el resultado de limpiar no contiene ninguna de las 6 columnas de la regla 1b (incluida `pass_status`).
- ☐ **La regla de 70:** una prueba fija que **69 pierde, 69,99 pierde y 70 aprueba**, y falla si el código usa `>` en vez de `>=` o vuelve al corte de 50 (comprobado con roturas deliberadas del código).
- ☐ `pytest` en verde desde la raíz del repo.

## 7. Criterios de cierre (H1)

- ☐ La limpieza corre **de principio a fin desde cero** (`data/processed/` borrada y regenerada con el notebook 03b), sin pasos manuales.
- ☐ Unidad de análisis y forma de partir **escritas** (sección 1) y documentadas en `reports/01_eda.md`.
- ☐ `pytest` en verde.
- ☐ Conjunto de prueba guardado y sin mirar.
- ☐ `data/raw/` intacta y `.env` fuera de Git (`git status`).
- ☐ Todo subido a GitHub.
- ☐ Revisaron el código de Claude con `checklist-revision-ia.md` y cada integrante puede explicar una función.
- ☐ **Hallazgo que no esperaban** (para la puesta en común): _______________ (candidato: varias variables casi no se relacionan con la nota —`private_tuition`, `internet_access`, `daily_screen_time`— y `study_method` está repartido en cinco partes iguales; ¿dataset sintético?)
