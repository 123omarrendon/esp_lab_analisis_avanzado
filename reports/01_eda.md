# Informe del EDA

> Resultado de `notebooks/02b_eda_aprueba_o_no.ipynb` (plantilla del curso: `02_eda.ipynb`). Cada hallazgo termina en una decisión,
> y cada decisión está implementada con pruebas en `src/proyecto/data/`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`.
> **Estado: borrador.** Las cifras las midió Claude sobre el CSV con la regla de **aprobar con 70 o más**; hay que confirmarlas al correr el notebook.
> Diccionario completo de variables: `data/README.md`.

## Qué son los datos

- **Filas × columnas:** 100.000 × 44 (`data/student_exam_performance.csv`, unos 25 MB)
- **Unidad de análisis (qué es una fila):** un estudiante (14 a 20 años) con sus hábitos de estudio, su contexto familiar y escolar, y el resultado de un examen.
- **¿Una entidad aparece en varias filas?** No: `student_id` tiene 100.000 valores distintos.
- **Objetivo y distribución:** `pass_70`, derivado de `exam_score`: `Pass` si la nota es **≥ 70** y `Fail` si es **< 70** (69 pierde el curso). `Fail` **69.210 (69,2 %)** y `Pass` 30.790 (30,8 %). Clase de interés: `Fail`. La columna `pass_status` del dataset usa el corte de 50 (`Fail` 22,6 %) y **no es el objetivo**.
- **Cambio de regla:** todos los que reprueban con 50 (22.611) también reprueban con 70, pero **46.599 estudiantes aprueban con 50 y pierden el curso con 70** (46,6 %).
- **Cerca del corte:** 2.224 estudiantes tienen una nota entre 69 y 70 y 24 sacan exactamente 70. **21,8 % está a menos de 5 puntos de 70** y de ellos pierde el curso 53,7 %: casi cara o cruz.
- **Línea base** (resultado de una regla trivial), con costos 5 a 1 (supuesto): «nunca avisar» cuesta 3,46 por estudiante, el azar 1,28 y **«avisar a todos» 0,31, la estrategia a vencer**. «Siempre `Fail`» acierta 69,2 % y «siempre `Pass`» 30,8 %. Un modelo supera a «avisar a todos» solo con **NPV > 83,3 %**.

## Calidad de los datos

- **Vacíos en 7 de 44 columnas:** `attendance_percentage` 9.863 (9,9 %), `time_management_score` 9.613 (9,6 %), `notes_quality` 8.407 (8,4 %), `previous_gpa` 7.793 (7,8 %), `sleep_quality` 6.994 (7,0 %), `parent_education` 6.526 (6,5 %), `device_availability` 2.965 (3,0 %). El resto está completo, incluido el objetivo. **41,9 % de las filas (41.940) tiene al menos un vacío.**
- **Los vacíos no anticipan el resultado:** `Fail` es 68,3 %–69,4 % con vacío y ≈ 69,2 % sin vacío.
- **Duplicados:** 0 filas repetidas (sin contar el id) y 0 ids repetidos.
- **Valores imposibles:** ninguno. `exam_score` va de 0 a 100 y `questions_correct` nunca supera a `questions_attempted`.
- **Extremos altos pero posibles:** `study_hours_per_day` llega a 12 (p99 = 8,4) y `online_learning_hours` a 15 (p99 = 9,2).
- **Variables truncadas arriba:** `stress_level` tiene 69,9 % de los valores en 10, `exam_anxiety_level` 38,6 % y `time_management_score` 7,4 % en 100.
- **Datos personales:** sin nombres ni documentos. Hay `student_id` (seudónimo) y atributos demográficos: `age` (incluye menores), `gender`, `family_income`, `parent_education`, `urban_rural`, `school_type`.
- **Posible origen sintético:** `private_tuition`, `internet_access`, `daily_screen_time`, `physical_activity_hours`, `online_course_hours` y `online_learning_hours` casi no se relacionan con el resultado (señal ≈ 0,50), y `study_method` se reparte casi exacto en cinco partes de ≈ 20 %. Es una sospecha: confirmar en la ficha de Kaggle.
- **Lo que sí se relaciona con perder el curso** (señal univariada, orientativa): `previous_exam_score` (0,73) y `previous_gpa` (0,72) son las más fuertes; siguen `study_hours_per_day`, `self_study_hours` y `practice_tests_completed`. Con `exam_difficulty`, `Fail` es 51,1 % si el examen es fácil y 85,1 % si es difícil.

## Sospechas de fuga de información

- `exam_score`: de ella se calcula el objetivo (`Pass` si ≥ 70).
- `pass_status`: **la misma respuesta con otro corte (50)**; sus 22.611 `Fail` son siempre `Fail` con 70. No es el objetivo y se excluye.
- `performance_grade` (A ≥ 85, B ≥ 75, C ≥ 65, D ≥ 50, F < 50) y `performance_level` (Low < 60, Medium < 80, High ≥ 80): derivadas de `exam_score`. Con el corte en 70 ya no reconstruyen el objetivo exacto (la letra `C` mezcla 11.713 `Fail` y 10.081 `Pass`; `Medium` mezcla), pero dan la respuesta exacta al **78,2 %** y al **58,0 %** de los estudiantes.
- `questions_correct`: correlación 0,975 con la nota; es el resultado del examen. `questions_attempted`: dato del propio examen, no existe antes de rendirlo.
- **A medir con y sin ellas (etapa 4):** `time_management_score`, `exam_anxiety_level`, `exam_difficulty`. Se miden en torno al examen y no se sabe aún si están disponibles al decidir.

## Decisiones

> Mínimo **5**. Cada una con una cifra que la respalda, una acción concreta y un motivo.
> Propuestas de Claude a partir de las cifras: el grupo debe revisarlas y aprobarlas (mismas que en `especificaciones/02-eda.md`).

| # | Hallazgo (con cifra) | Decisión | Motivo |
|---|---|---|---|
| 1 | El objetivo `pass_70` sale de `exam_score`; `pass_status` es la misma respuesta con corte en 50; `performance_grade` da la respuesta exacta a 78,2 % y `performance_level` a 58,0 %; `questions_correct` correlaciona 0,975 con la nota | **Crear `pass_70` y luego quitar** `exam_score`, `pass_status`, `performance_grade`, `performance_level`, `questions_correct` y `questions_attempted` de las variables de entrada | Contienen la respuesta o solo se conocen al rendir el examen: darían un modelo perfecto en papel e inútil al decidir |
| 2 | 7 columnas con vacíos (3,0 % a 9,9 %); `Fail` con vacío 68,3–69,4 % frente a ≈ 69,2 % sin vacío | No borrar filas; resolver los vacíos dentro del `Pipeline` (etapa 4) | Borrar las filas con algún vacío eliminaría 41.940 estudiantes (41,9 %); el vacío no anticipa el resultado |
| 3 | `student_id` único (100.000 ids); 0 duplicados | Partir por fila, estratificado por `pass_70`; excluir `student_id` del modelo | Ningún estudiante cae en dos particiones; se mantiene el 69,2 % de `Fail` en ambas |
| 4 | `Fail` = 69,2 %: «avisar a todos» acierta 69,2 % y cuesta 0,31; «nunca avisar» cuesta 3,46; 21,8 % está a menos de 5 puntos del corte | Evaluar con costo por estudiante, *recall* de `Fail` y NPV (≥ 83,3 %), con precisión > 69,2 %; no con exactitud | Con la mayoría reprobada, la exactitud y el *recall* solos se «ganan» avisando a todos |
| 5 | Extremos plausibles (12 h de estudio, 15 h en línea) y 0 valores fuera de rango | Conservar los extremos; volver vacío todo valor fuera de rango que aparezca en datos nuevos | Son posibles, no errores; las reglas de rango protegen la app de entradas imposibles |
| 6 | `gender` (`Other` 2,0 %) y otros atributos sensibles (`age`, `family_income`, `parent_education`, `urban_rural`, `school_type`) | `gender` no entra como predictor; auditar *recall*, precisión y NPV de `Fail` por grupo en la validación | No debe decidir quién recibe apoyo según un atributo sensible; hay que comprobar que el modelo no falle más con un grupo |
| 7 | `stress_level` tiene 69,9 % de los valores en 10 y `exam_anxiety_level` 38,6 %; `time_management_score` 7,4 % en 100 | Conservar sin recortar ni transformar | No son errores: están truncadas arriba |
| 8 | `self_study_hours` ≤ `study_hours_per_day` en el 100 % de las filas; sumar las tres columnas de horas da 63 estudiantes con más de 24 h | No crear una variable sumando las horas; probar `self_study_hours / study_hours_per_day` | Sumar duplicaría horas |
| 9 | `previous_exam_score` (`Fail` 90,7 % → 41,7 % del quintil más bajo al más alto), `previous_gpa` (89,6 % → 43,1 %), `exam_difficulty` (51,1 % → 85,1 %); 7 numéricas con señal ≈ 0,50 | Conservar todas como candidatas; medir en la etapa 4 con validación cruzada | El EDA usa todos los datos; la selección se decide con validación |
| 10 | `family_income`: `Fail` 75,5 % (bajo) vs 60,5 % (alto), brecha de 15 puntos que persiste dentro de cada dificultad | No usarla como predictor por defecto (ni `gender`); auditar por grupo y medir cuánto cuesta excluirla | No debe avisar distinto según la riqueza de la familia; puede haber variables sustitutas |

> Cifras y código: `notebooks/02b_eda_aprueba_o_no.ipynb`. **Corrección:** una idea previa de variable, `total_study_hours` (suma de las tres columnas de horas), se descarta por duplicar horas (decisión 8).

## Qué queda abierto

- Medir el modelo **con y sin** `time_management_score`, `exam_anxiety_level` y `exam_difficulty` para decidir si se conocen antes del examen.
- Decidir en grupo si `parent_education`, `urban_rural`, `school_type` y `age` entran como predictores o solo como variables de auditoría (`gender` y `family_income` ya salen).
- Validar con la institución el supuesto de costos 5 a 1 y estimar su capacidad real de tutoría: no se puede apoyar al 69 % de los estudiantes.
- Confirmar la licencia del dataset y si es sintético.
- Decidir si el CSV se mueve a `data/raw/` (lo pide la estructura del curso) y si se sigue subiendo al repositorio (25 MB).
- Clasificación (`pass_70`) frente a regresión (`exam_score`): la propuesta es clasificar; el grupo decide.
