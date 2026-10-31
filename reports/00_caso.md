# Ficha de caso

> Instrucciones y un ejemplo completo (CreditSight): `material-del-curso/evaluacion/ficha-de-caso.md`.
> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.
> Variables y cifras: `data/README.md`. Detalle del caso: `especificacion-proyecto.md`.

- **case_id:** rendimiento-estudiantil
- **business_question:** El/la coordinador(a) académico(a) decide qué estudiantes recibirán tutoría o refuerzo antes del examen final. Con los hábitos de estudio, asistencia, historial académico y contexto de cada estudiante, el modelo estima quiénes tienen más probabilidad de no aprobar, para que el equipo revise esos casos. No sanciona ni excluye a nadie.
- **dataset_source:** Student Exam Performance & Success Dataset (Mobeen Fatimah), https://www.kaggle.com/datasets/mobeenfatimah/student-exam-performance-and-success-dataset. Licencia: pendiente de verificar.
- **dataset_rows:** 100.000
- **dataset_columns:** 44
- **target:** `pass_70`, derivado de `exam_score`: `Pass` si la nota es **≥ 70**, `Fail` si es **< 70** (69 pierde el curso). `Fail` 69,2 % (69.210) / `Pass` 30,8 % (30.790); clase de interés `Fail`. La columna `pass_status` del dataset usa el corte de 50 y no es el objetivo.
- **problem_type:** clasificación
- **primary_metric:** **costo esperado por estudiante**, ***recall* de `Fail`** y **NPV**. El error más caro es no avisar a quien pierde el curso; pero el *recall* solo se «gana» avisando a todos y la exactitud no sirve ("siempre Fail" acierta 69,2 %), por eso se leen juntos.
- **business_cost_note:** Falso negativo (no avisar a quien reprobará): el estudiante pierde el apoyo a tiempo y puede perder la asignatura. Falso positivo (avisar a quien aprobaba): se gasta una tutoría y el estudiante se preocupa sin necesidad. No cuestan lo mismo; los costos exactos los define la institución. **Supuesto de trabajo (`notebooks/01b_caso_negocio_aprueba_o_no.ipynb`): falso negativo : falso positivo = 5 : 1**, que no sale del dataset y debe validarse. Con él, sin modelo cuesta 3,46 por estudiante no avisar a nadie, 1,28 el azar y **0,31 avisar a todos, la estrategia a vencer**. Un modelo la supera solo si su NPV es mayor que 83,3 %. Con la mayoría reprobada (69,2 %), «avisar a todos» es mejor que «no avisar a nadie» con cualquier proporción mayor que 0,44 a 1. Como no se puede dar tutoría al 69 % de los estudiantes, falta estimar la capacidad real de la institución.
- **status:** borrador
- **reviewer_notes:** <!-- las llena el instructor -->
