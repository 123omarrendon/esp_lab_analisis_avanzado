# Especificación del proyecto

> Complétenla en el grupo y manténganla actualizada. Claude la lee antes de generar
> código: lo que escriban aquí manda sobre cualquier otra suposición.
> Las variables y cifras del dataset están en [`data/README.md`](data/README.md).

## 1. Grupo

| Integrante | Rol (datos / modelado / app / negocio) |
|---|---|
| | |
| | |
| | |

Nombre de la "startup": _______________   Repositorio (público): https://github.com/123omarrendon/esp_lab_analisis_avanzado

## 2. Caso de negocio

- **Pregunta de negocio** (una frase, que alguien sin formación técnica entienda): ¿Qué estudiantes tienen más probabilidad de **perder el curso** (sacar menos de 70 en el examen) para ofrecerles apoyo antes de que lo presenten? **Regla: aprueba con 70 o más; con menos de 70 (69 o 69,99) pierde el curso.**
- **¿Quién usará el resultado y qué decisión tomará con él?** El/la coordinador(a) académico(a) priorizará qué estudiantes recibirán tutoría o refuerzo antes del examen. El resultado es una alerta para revisión humana, no una sanción.
- **¿Qué cuesta equivocarse?** Es peor un **falso negativo** (no avisar de un estudiante que pierde el curso: pierde el apoyo a tiempo) que un **falso positivo** (ofrecer una tutoría que no hacía falta). **Supuesto de trabajo: 5 a 1** (`notebooks/01b_caso_negocio_aprueba_o_no.ipynb`); los costos exactos los define la institución y no salen del dataset.

## 3. Datos

- **Fuente** (enlace de Kaggle, empresa, etc.): [Student Exam Performance & Success Dataset](https://www.kaggle.com/datasets/mobeenfatimah/student-exam-performance-and-success-dataset) (Mobeen Fatimah)
- **Filas / columnas:** 100.000 / 44 (`data/student_exam_performance.csv`)
- **Variable objetivo** (columna que queremos predecir o describir): **`pass_70`**, derivada de `exam_score` (`Pass` si la nota es ≥ 70; `Fail` si es < 70): `Fail` **69,2 %** (69.210) / `Pass` 30,8 % (30.790). Clase de interés: `Fail`. **La columna `pass_status` del dataset usa el corte de 50: no es el objetivo y se excluye como fuga.**
- **Tipo de problema:** ☑ clasificación (binaria)  ☐ regresión  ☐ clusterización
  - Decisión propuesta: la acción (dar apoyo o no) es de sí/no, y `pass_70` la expresa directamente. `exam_score` (nota 0–100) queda como alternativa de regresión si el grupo prefiere estimar la nota.
- **¿Una misma entidad (cliente, paciente, empresa) aparece en varias filas?** ☑ no → `student_id` es único (100.000 ids distintos). La partición será por: **fila, estratificada por `pass_70`**.
- **Datos personales o confidenciales presentes:** ☑ sí, de tipo demográfico (no hay nombres ni documentos): `age` (14–20, incluye menores), `gender`, `family_income`, `parent_education`, `urban_rural`, `school_type`. Se tratarán así: `student_id` se excluye del modelo; `gender` y `family_income` no entran como predictores (`family_income` tiene una brecha de 15 puntos en `Fail`); las demás se usan solo si se justifica y siempre se audita el desempeño por grupo.
- **Datos que no se pueden usar para predecir (fuga):** `exam_score`, `pass_status` (la misma respuesta con corte en 50), `performance_grade`, `performance_level` (derivadas de la nota), `questions_correct` y `questions_attempted` (datos del propio examen). Detalle en `data/README.md`.
- **Licencia o permiso de uso de los datos:** pendiente de verificar en Kaggle.

## 4. Métrica

- **Métricas principales:** **costo esperado por estudiante** (con 5 a 1), ***recall* de `Fail`** (de los que pierden el curso, cuántos detectamos) y **NPV** (de los que el modelo deja «tranquilos», cuántos aprueban de verdad). **Por qué:** el error caro es no avisar a quien pierde el curso, pero el *recall* solo se «gana» avisando a todos y la exactitud no sirve (siempre `Fail` ya acierta 69,2 %).
- **Métricas secundarias:** precisión de `Fail` (debe superar la tasa base de 69,2 %), F1 y F2, especificidad, exactitud balanceada, PR-AUC, calibración, alertas por cada 100 estudiantes y *recall* / precisión en el top k % (capacidad de tutoría).
- **Línea base** (qué resultado obtiene una regla simple o un modelo trivial): con 5 a 1, «nunca avisar» cuesta 3,46 por estudiante, el azar 1,28 y **«avisar a todos» 0,31, la estrategia a vencer**. Un modelo la supera solo si su costo es menor que 0,31, lo que equivale a un **NPV mayor que 83,3 %**.

## 5. Riesgos

- Fuga de información posible: `exam_score`, `pass_status`, `performance_grade`, `performance_level`, `questions_correct`, `questions_attempted`. A medir con y sin ellas: `time_management_score`, `exam_anxiety_level`, `exam_difficulty` (confirmar si se conocen antes del examen).
- Sesgos o equidad: `gender`, `age`, `family_income`, `parent_education`, `urban_rural`, `school_type`. `family_income` es el atributo con diferencia grande (`Fail` 75,5 % con ingreso bajo vs 60,5 % con alto). Comparar *recall*, precisión y NPV de `Fail` entre grupos antes de dar el modelo por válido.
- Datos faltantes o de mala calidad: 7 columnas con vacíos (3,0 % a 9,9 %): `parent_education`, `previous_gpa`, `attendance_percentage`, `notes_quality`, `sleep_quality`, `device_availability`, `time_management_score`. Posible origen sintético del dataset (a confirmar).
- Límites de lo que el modelo puede decir: 21,8 % de los estudiantes está a menos de 5 puntos del corte de 70 (53,7 % de ellos pierde el curso), así que el resultado cerca del corte es casi aleatorio. Estima una probabilidad de no aprobar, no explica causas ni garantiza el futuro de un estudiante. No debe usarse para sancionar, excluir ni limitar oportunidades.

## 6. Entregables y fechas

| Hito | Contenido | Fecha |
|---|---|---|
| H1 | Ficha aprobada, EDA y preprocesamiento reproducible | Cierre de la clase 2 (vie 30 oct) |
| H2 | Torneo, optimización con tracking, modelo registrado, repo modular, app local | Cierre de la clase 4 (jue 5 nov) |
| H3 | App desplegada y presentación (≤ 5 diapositivas) | Clase 5 (vie 6 nov) |
| H4 | Informe técnico final (hasta 8 días tras la última clase) | Domingo 15 nov |

## 7. Decisiones tomadas (agréguenlas a medida que avancen)

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-10-31 | **Regla de aprobación: 70.** Objetivo = `pass_70` (`Fail` si `exam_score` < 70), clasificación binaria, clase de interés `Fail` | La institución define que se aprueba con 70 o más; `Fail` es el 69,2 % de los casos. Reemplaza al corte de 50 (22,6 %) |
| 2026-10-31 | Excluir `exam_score`, `pass_status` (corte 50), `performance_grade`, `performance_level`, `questions_correct`, `questions_attempted` | Contienen o derivan de la respuesta, o se conocen al rendir el examen. El objetivo se crea **antes** de quitar `exam_score` |
| 2026-10-31 | Partir por fila, estratificado por `pass_70` | `student_id` es único: no hay estudiantes repetidos |
| 2026-10-31 | Métricas principales = costo por estudiante, *recall* de `Fail` y NPV; la estrategia a vencer es «avisar a todos» (0,31) | Un falso negativo cuesta más (supuesto 5 a 1); con 69,2 % de `Fail`, la exactitud y el *recall* solos se «ganan» avisando a todos |
| 2026-10-31 | Etapa 4: ninguna variable nueva (`self_study_share`, `prep_total_hours`); sin indicador de vacío; quitar 7 columnas sin señal (28 variables) | Medido con LightGBM fijo y 5 pliegues por fila: todas dentro del ruido (costo 0,2584 frente a 0,2579 de la referencia). Detalle en `reports/04_features.md` |
| 2026-10-31 | Conservar `exam_difficulty` **condicionada a que se conozca al avisar** (por confirmar con la institución) | Sin ella el costo sube de 0,258 a 0,283 (≥ 9 veces el ruido): se pierde la mitad de la ventaja sobre «avisar a todos». Si no se conoce antes, es fuga |
| 2026-10-31 | Etapa 5: finalistas = regresión logística y LightGBM; se descartan random forest y XGBoost | Regresión logística, LightGBM y XGBoost empatan en costo (0,258; diferencia 0,1–0,2 veces el ruido); random forest pierde en los 5 pliegues (0,283); XGBoost empata con LightGBM y es más lento. Desempate por simplicidad e interpretabilidad. Detalle en `reports/05_torneo.md` |
| 2026-10-31 | `gender` y `family_income` no entran como predictores; se usan para auditar equidad | Atributos sensibles; `family_income` tiene 15 puntos de brecha en `Fail`. No debe influir en quién recibe apoyo |

> Estas decisiones las propuso Claude a partir de las cifras del CSV: el grupo debe revisarlas y aprobarlas o cambiarlas.
