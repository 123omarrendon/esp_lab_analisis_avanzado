# Datos del proyecto

**Archivo:** `data/student_exam_performance.csv` · **100.000 filas × 44 columnas** · **Fuente:** [Student Exam Performance & Success Dataset (Kaggle, Mobeen Fatimah)](https://www.kaggle.com/datasets/mobeenfatimah/student-exam-performance-and-success-dataset) · **Licencia:** por verificar en la página de Kaggle antes de redistribuir.

> Todas las cifras de este documento se midieron sobre el CSV (100.000 filas). Si cambia el archivo, hay que volver a medirlas.
> Este diccionario es la **fuente única** de las variables: los demás `.md` lo citan, no lo repiten.

## Qué representa una fila y cuál es el objetivo

- **Una fila = un estudiante** (14 a 20 años) con sus hábitos, contexto y el resultado de un examen. `student_id` es único (100.000 valores distintos): ningún estudiante se repite.
- **Regla de aprobación del caso:** el estudiante **aprueba con 70 o más** y **pierde el curso con menos de 70** (69 y 69,99 pierden; 70,00 aprueba).
- **Objetivo (`TARGET`): `pass_70`** (columna **derivada**, no viene en el CSV; la crea `add_target` en `src/proyecto/data/cleaning.py` a partir de `exam_score`) → `Fail` (69.210 = **69,2 %**) / `Pass` (30.790 = 30,8 %). **Clase de interés: `Fail`** (estudiante que necesitaría apoyo).
- **`pass_status` del dataset NO es el objetivo:** usa el corte de **50** (`Fail` 22.611 = 22,6 %). Todos sus `Fail` también lo son con 70, pero **46.599 estudiantes aprueban con 50 y pierden el curso con 70**. Se trata como una columna de fuga.
- `exam_score` y sus derivadas no pueden usarse para predecir el objetivo.
- **Momento de la decisión:** antes del examen final. Solo sirven como predictores las variables que ya se conocen en ese momento.

## Diccionario de variables

**Rol:** `ID` identificador · `OBJ` objetivo · `FUGA` no se usa (contiene o deriva de la respuesta, o se conoce después) · `REVISAR` se mide en torno al examen: se prueba con y sin ella (etapa 4) · `SENS` atributo sensible: no entra como predictor por defecto y se usa para auditar equidad · `PRED` predictor candidato.

| Variable | Tipo | Rol | Vacíos | Nota |
|---|---|---|---|---|
| `student_id` | texto | ID | 0 | `STU_000001`…; se excluye del modelo |
| `pass_70` | categórica (2), **derivada** | **OBJ** | 0 | Pass (≥ 70) 30,8 % / Fail (< 70) 69,2 %; no está en el CSV |
| `pass_status` | categórica (2) | FUGA | 0 | Mismo resultado con **corte en 50** (Pass 77,4 % / Fail 22,6 %); no es el objetivo |
| `exam_score` | número 0–100 | FUGA | 0 | Nota del examen; de ella se deriva el objetivo |
| `performance_grade` | categórica (A–F) | FUGA | 0 | Letra por rango de `exam_score` (A ≥ 85, B ≥ 75, C ≥ 65, D ≥ 50, F < 50). Con el corte en 70 da la respuesta exacta al 78,2 % (solo `C` mezcla `Fail` y `Pass`) |
| `performance_level` | categórica (3) | FUGA | 0 | Low < 60, Medium 60–79,99, High ≥ 80 de `exam_score`. Da la respuesta exacta al 58,0 % (`Medium` mezcla) |
| `questions_correct` | entero | FUGA | 0 | Se conoce al rendir el examen; correlación 0,975 con `exam_score` |
| `questions_attempted` | entero | FUGA | 0 | Dato del propio examen; correlación ≈ 0 con la nota, pero no existe antes de rendirlo |
| `age` | entero 14–20 | SENS | 0 | Hay menores de edad |
| `gender` | Male 49,1 % / Female 48,8 % / Other 2,0 % | SENS | 0 | |
| `education_level` | High School 59,8 % / Undergraduate 40,2 % | PRED | 0 | |
| `school_type` | Public 55,1 % / Private 34,9 % / Charter 10,0 % | SENS | 0 | Contexto socioeconómico |
| `family_income` | Low, Lower-Middle, Middle, Upper-Middle, High | SENS | 0 | Middle 30,1 % |
| `parent_education` | High School, Associate, Bachelor, Master, Doctorate | SENS | 6.526 (6,5 %) | |
| `urban_rural` | Urban 45,0 % / Suburban 35,1 % / Rural 19,9 % | SENS | 0 | |
| `previous_exam_score` | número 30–100 | PRED | 0 | Mayor correlación legítima con `exam_score` (0,49) |
| `previous_gpa` | número 1–4 | PRED | 7.793 (7,8 %) | Correlación 0,47 |
| `attendance_percentage` | número 46,3–100 | PRED | 9.863 (9,9 %) | |
| `assignment_completion_rate` | número 20–100 | PRED | 0 | |
| `class_participation` | Low / Medium / High | PRED | 0 | |
| `study_hours_per_day` | número 0,5–12 | PRED | 0 | p99 = 8,4 h; máximo plausible |
| `self_study_hours` | número 0,25–10 | PRED | 0 | |
| `private_tuition` | 0 / 1 (30 % sí) | PRED | 0 | Correlación ≈ 0 |
| `online_learning_hours` | número 0–15 | PRED | 0 | p99 = 9,2 h; correlación ≈ 0 |
| `study_consistency` | Low / Medium / High | PRED | 0 | |
| `study_environment` | Quiet / Moderate / Noisy | PRED | 0 | |
| `study_method` | Flashcards, Summarizing, Group Study, Practice Tests, Self-Reading | PRED | 0 | Cinco categorías de ≈ 20 % cada una |
| `revision_frequency` | Daily / Weekly / Rarely | PRED | 0 | |
| `practice_tests_completed` | entero 0–20 | PRED | 0 | |
| `notes_quality` | Poor / Average / Excellent | PRED | 8.407 (8,4 %) | |
| `sleep_hours` | número 3–11 | PRED | 0 | |
| `sleep_quality` | Poor / Fair / Good / Excellent | PRED | 6.994 (7,0 %) | |
| `daily_screen_time` | número (horas) | PRED | 0 | Correlación ≈ 0 |
| `physical_activity_hours` | número (horas) | PRED | 0 | Correlación ≈ 0 |
| `break_frequency` | Rarely / Occasionally / Frequently | PRED | 0 | |
| `stress_level` | entero | PRED | 0 | Correlación −0,16 |
| `motivation_level` | Low / Medium / High | PRED | 0 | |
| `internet_access` | 0 / 1 | PRED | 0 | Correlación ≈ 0 |
| `device_availability` | Dedicated 71,9 % / Shared 25,2 % | PRED | 2.965 (3,0 %) | |
| `educational_app_usage` | Low / Moderate / High | PRED | 0 | |
| `online_course_hours` | número (horas) | PRED | 0 | Correlación ≈ 0 |
| `exam_difficulty` | Easy / Medium / Hard | REVISAR | 0 | Debería conocerse antes del examen: confirmarlo |
| `exam_preparation_days` | entero | PRED | 0 | Correlación 0,20 |
| `time_management_score` | número | REVISAR | 9.613 (9,6 %) | Puede medirse con el examen: confirmar cuándo |
| `exam_anxiety_level` | número | REVISAR | 0 | Se mide en torno al examen; correlación −0,13 |

Las correlaciones son con `exam_score` (la nota numérica), no con el objetivo `pass_70`; sirven solo como orientación para el EDA.

## Calidad de los datos (resumen medido)

- **Duplicados:** 0 filas repetidas (sin contar `student_id`); 0 ids repetidos.
- **Vacíos:** 7 columnas (tabla anterior). La tasa de `Fail` con vacío (68,3 %–69,4 %) es casi igual a la de sin vacío (≈ 69,2 %): no se ve que el vacío anticipe el resultado.
- **Valores imposibles:** ninguno encontrado (`questions_correct` nunca supera a `questions_attempted`; las notas están entre 0 y 100).
- **Extremos:** los máximos de horas de estudio (12) y de aprendizaje en línea (15) son altos pero posibles.
- **Filas con vacíos:** 41,9 % de las filas (41.940) tiene al menos un vacío; borrarlas sería perder casi la mitad de los estudiantes.
- **Variables truncadas arriba:** `stress_level` (69,9 % de los valores en 10), `exam_anxiety_level` (38,6 % en 10), `time_management_score` (7,4 % en 100).
- **Horas de estudio:** `self_study_hours` ≤ `study_hours_per_day` en el 100 % de las filas (parece una parte de ella): no sumarlas.
- **Cerca del corte:** 21,8 % de los estudiantes está a menos de 5 puntos de 70 y de ellos 53,7 % pierde el curso (casi cara o cruz).
- **Señal sobre `Fail` (corte en 70):** `previous_exam_score` (`Fail` 90,7 % → 41,7 % del quintil más bajo al más alto), `previous_gpa` (89,6 % → 43,1 %) y `exam_difficulty` (51,1 % fácil → 85,1 % difícil) son las más fuertes; `family_income` tiene una brecha de **15 puntos** (75,5 % con ingreso bajo, 60,5 % con alto). Detalle en `notebooks/02b_eda_aprueba_o_no.ipynb`.
- **Posible origen sintético:** varias variables casi no se relacionan con la nota (correlación ≈ 0) y `study_method` está repartido casi exacto en cinco partes iguales. Es una sospecha, no una conclusión: verificarlo en la ficha de Kaggle.

## Qué hacer con el CSV

- La estructura del curso pide los datos originales en `data/raw/` (nunca se modifican). Hoy el CSV está en `data/`; decidir en grupo si se mueve.
- El CSV pesa unos 25 MB. Si la licencia no permite redistribuirlo, dejar solo las instrucciones de descarga y quitarlo del repositorio.
