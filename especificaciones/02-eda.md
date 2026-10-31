# Especificación · Etapa 2 · EDA

> Se llena **antes** de abrir `notebooks/02_eda.ipynb` (las secciones 1 y 2) y se completa **mientras**
> lo ejecutan (3 y 4). El resultado final, con las decisiones, va a `reports/01_eda.md`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md` · Ejemplo: `material-del-curso/ejemplo-creditsight/reports/01_eda.md`.
> Variables y cifras del dataset: `data/README.md`.

**Grupo:** _______________   **Fecha:** 2026-10-30   **Estado:** ☑ borrador  ☐ cerrada

## 1. Qué esperamos encontrar (se escribe ANTES de mirar los datos)

Una hipótesis por pregunta. Si después no se cumple, es un hallazgo: anótenlo.

> **Pendiente del grupo.** Esta sección son *sus* hipótesis y solo valen si se escriben antes de ver las cifras.
> Claude ya perfiló el CSV para llenar las secciones 2 a 4, así que no la completó por ustedes.
> Las cifras ya medidas están en `data/README.md`: si las leen primero, anótenlo aquí.

| Pregunta | Lo que creemos |
|---|---|
| ¿Qué representa una fila? | |
| ¿Alguna entidad se repite en varias filas? | |
| ¿Qué variable **debería** ser estable y no cambiar? | |
| ¿Qué significaría un vacío en nuestras columnas clave? | |
| ¿Qué columna solo se conoce **después** de la decisión que queremos apoyar? | |

## 2. Qué vamos a medir

Marquen lo que aplica a su dataset. Lo que no aplique se tacha **con una razón** (no se deja en blanco).

| Chequeo (guía, sección 3) | ¿Aplica? | Columnas a revisar | Quién lo hace |
|---|---|---|---|
| 3.1 Números guardados como texto | ☐ sí ☑ no: las 22 columnas numéricas se leyeron como número (`int64`/`float64`) | — | |
| 3.2 Valores centinela (`-1`, `9999`, `?`) | ☑ sí | Mínimos y máximos de todas las numéricas (el perfil inicial no mostró centinelas; confirmarlo en el notebook) | |
| 3.3 Valores imposibles (percentiles, negativos) | ☑ sí | `exam_score` (0–100), `attendance_percentage`, `assignment_completion_rate`, `previous_exam_score` (0–100), `previous_gpa` (1–4), `sleep_hours`, `questions_correct` ≤ `questions_attempted` | |
| 3.4 Constancia por entidad | ☐ sí ☑ no: no hay entidades repetidas, `student_id` es único | — | |
| 3.5 Vacíos que significan algo | ☑ sí | `parent_education`, `previous_gpa`, `attendance_percentage`, `notes_quality`, `sleep_quality`, `device_availability`, `time_management_score` | |
| 3.6 Duplicados | ☑ sí | Filas completas sin `student_id` y `student_id` | |
| 3.7 Fechas y orden temporal | ☐ sí ☑ no: el dataset no trae fechas ni periodo | — | |
| 3.8 Categorías raras / alta cardinalidad | ☑ sí | `gender` (`Other` = 2,0 %); el resto tiene entre 2 y 5 categorías | |
| 3.9 Identidad y datos personales | ☑ sí | `student_id` (seudónimo), `age` (menores), `gender`, `family_income`, `parent_education`, `urban_rural`, `school_type` | |

## 3. Lo que medimos (se llena mientras corre el notebook)

> Cifras ya medidas por Claude sobre el CSV, con la regla de **aprobar con 70 o más** (`pass_70`). Confirmarlas al correr `notebooks/02b_eda_aprueba_o_no.ipynb`.

- **Filas × columnas:** 100.000 × 44
- **Unidad de análisis (una frase):** un estudiante (14 a 20 años) con sus hábitos de estudio, su contexto y el resultado de un examen.
- **Columna que identifica a la entidad (`ID_COL`):** `student_id`   **¿Se repite?** ☑ no (100.000 ids distintos)
- **Objetivo (`TARGET`):** `pass_70` (derivado de `exam_score`: `Pass` si ≥ 70, `Fail` si < 70)   **Distribución:** `Fail` 69.210 (69,2 %) / `Pass` 30.790 (30,8 %). `pass_status` (corte en 50) **no es el objetivo**.
- **Línea base** (regla trivial) y su resultado: con costos 5 a 1, «nunca avisar» cuesta 3,46 por estudiante, el azar 1,28 y **«avisar a todos» 0,31 (la estrategia a vencer)**; un modelo la supera solo con NPV > 83,3 %. «Siempre `Fail`» acierta 69,2 % y «siempre `Pass`» 30,8 %.
- **Vacíos en el objetivo:** 0   **Qué haremos con esas filas:** no aplica.
- **Datos personales encontrados:** no hay nombres ni documentos; sí `student_id` (seudónimo) y atributos demográficos (`age`, `gender`, `family_income`, `parent_education`, `urban_rural`, `school_type`).
- **Columnas sospechosas de fuga:** `exam_score`, `pass_status` (la misma respuesta con corte en 50), `performance_grade` (da la respuesta exacta al 78,2 %) y `performance_level` (58,0 %), derivadas de la nota, `questions_correct` (correlación 0,975 con la nota) y `questions_attempted` (dato del examen). Además, a medir con y sin ellas en la etapa 4: `time_management_score`, `exam_anxiety_level`, `exam_difficulty`.

## 4. Decisiones (mínimo 5)

> Cada una con **cifra**, acción **concreta** y **motivo**. Se copian tal cual a `reports/01_eda.md`.
> Cada decisión se convierte en una función de `src/proyecto/data/` y en una prueba (ver `03-preprocesamiento.md`).
> Propuestas de Claude a partir de las cifras: el grupo debe revisarlas y aprobarlas.

| # | Hallazgo (con cifra) | Decisión | Motivo | Función que la implementa |
|---|---|---|---|---|
| 1 | El objetivo `pass_70` sale de `exam_score` (`Pass` si ≥ 70). `pass_status` es la misma respuesta con corte en 50 (sus 22.611 `Fail` son siempre `Fail` con 70); `performance_grade` da la respuesta exacta a 78,2 % y `performance_level` a 58,0 %; `questions_correct` correlaciona 0,975 con la nota | **Crear `pass_70` y luego quitar** `exam_score`, `pass_status`, `performance_grade`, `performance_level`, `questions_correct` y `questions_attempted` de las variables de entrada | Contienen la respuesta o solo se conocen al rendir el examen: dan un modelo perfecto en papel e inútil al decidir | `add_target`, `drop_leakage_columns` |
| 2 | 7 columnas con vacíos: 9,9 % `attendance_percentage`, 9,6 % `time_management_score`, 8,4 % `notes_quality`, 7,8 % `previous_gpa`, 7,0 % `sleep_quality`, 6,5 % `parent_education`, 3,0 % `device_availability`. `Fail` con vacío: 68,3–69,4 %; sin vacío: ≈ 69,2 % | No borrar filas. Dejar los vacíos y resolverlos dentro del `Pipeline` (etapa 4) | Borrar las filas con algún vacío eliminaría 41.940 estudiantes (41,9 %); el vacío no anticipa el resultado | `check_missing_report` |
| 3 | `student_id` es único (100.000 ids); 0 filas duplicadas sin el id | No agrupar ni deduplicar: partir por fila, estratificado por `pass_70`. Excluir `student_id` del modelo | Ningún estudiante aparece en dos particiones (se mantiene el 69,2 % de `Fail` en ambas); el id no explica el resultado | `split_train_test`, `drop_identifier` |
| 4 | `Fail` = 69,2 %: «avisar a todos» acierta 69,2 % y cuesta 0,31 (la mejor línea base); «nunca avisar» cuesta 3,46; 21,8 % está a menos de 5 puntos del corte (53,7 % pierde) | Evaluar con costo por estudiante, *recall* de `Fail` y NPV (≥ 83,3 %), con precisión > 69,2 %; no con exactitud; estratificar la partición | Con la mayoría reprobada, la exactitud y el *recall* solos se «ganan» avisando a todos | `split_train_test` |
| 5 | Extremos plausibles: `study_hours_per_day` máx. 12 (p99 8,4), `online_learning_hours` máx. 15 (p99 9,2); 0 valores fuera de rango (`exam_score` 0–100, `questions_correct` ≤ `questions_attempted`) | Conservar los extremos y no recortar. Volver vacío todo valor fuera de rango que aparezca en datos nuevos | Son valores posibles, no errores; las reglas de rango protegen la app frente a entradas imposibles | `mark_out_of_range` |
| 6 | `gender` (3 categorías, `Other` 2,0 %) y otros atributos sensibles (`age` 14–20, `family_income`, `parent_education`, `urban_rural`, `school_type`) | `gender` y `family_income` no entran como predictores. Auditar *recall*, precisión y NPV de `Fail` por `gender`, `family_income`, `urban_rural` y `school_type` en la validación | El modelo no debe decidir quién recibe apoyo según un atributo sensible; hay que comprobar que no falle más con un grupo | `drop_sensitive_columns` |
| 7 | `stress_level` tiene 69,9 % de los valores en 10 y `exam_anxiety_level` 38,6 %; `time_management_score` 7,4 % en 100 | Conservar sin recortar ni transformar | No son errores: están truncadas arriba | — (sin función) |
| 8 | `self_study_hours` ≤ `study_hours_per_day` en el 100 % de las filas; sumar las tres columnas de horas da 63 estudiantes con más de 24 h | No crear una variable sumando las horas; probar `self_study_hours / study_hours_per_day` | Sumar duplicaría horas | — (etapa 4) |
| 9 | `previous_exam_score` (`Fail` 90,7 % → 41,7 % del quintil más bajo al más alto), `previous_gpa` (89,6 % → 43,1 %), `exam_difficulty` (51,1 % → 85,1 %); 7 numéricas con señal ≈ 0,50 | Conservar todas como candidatas; medir en la etapa 4 con validación cruzada | El EDA usa todos los datos; la selección se decide con validación | — (etapa 4) |
| 10 | `family_income`: `Fail` 75,5 % (bajo) vs 60,5 % (alto), brecha de 15 puntos que persiste dentro de cada dificultad | No usarla como predictor por defecto; auditar por grupo y medir cuánto cuesta excluirla | No debe avisar distinto según la riqueza de la familia; puede haber variables sustitutas | `drop_sensitive_columns` |

> Detalle y código que produce estas cifras: `notebooks/02b_eda_aprueba_o_no.ipynb`.

## 5. Criterios de cierre

- ☐ `notebooks/02_eda.ipynb` corre de principio a fin sin errores.
- ☐ Unidad de análisis y `ID_COL` declarados por escrito (sección 3).
- ☐ Al menos **5 decisiones** con cifra, acción y motivo.
- ☐ Datos personales identificados y plan para eliminarlos al cargar.
- ☐ Valores imposibles, centinelas y significado de los vacíos revisados.
- ☐ Fuga sospechada: lista escrita, aunque sea "ninguna, porque…".
- ☐ `reports/01_eda.md` completado.
- ☐ Quien **no** escribió una decisión sabe explicar por qué se tomó.
