# Predicción del rendimiento y éxito académico de estudiantes

## 1. Descripción del proyecto

Este proyecto propone utilizar técnicas de análisis de datos y *Machine Learning* para apoyar la toma de decisiones en una institución educativa. El propósito es identificar estudiantes que podrían presentar bajo rendimiento académico o riesgo de no alcanzar los resultados esperados, para que el equipo académico pueda evaluar intervenciones oportunas, como tutorías, acompañamiento o refuerzos.

El modelo debe utilizarse como una herramienta de apoyo y no como un mecanismo automático para sancionar, excluir o limitar oportunidades educativas.

## 2. Fuente de datos

- **Dataset:** [Student Exam Performance & Success Dataset — Kaggle](https://www.kaggle.com/datasets/mobeenfatimah/student-exam-performance-and-success-dataset)
- **Autor en Kaggle:** Mobeen Fatimah.
- **Archivo:** `data/student_exam_performance.csv` — 100.000 estudiantes (una fila cada uno) y 44 columnas. Diccionario de variables, roles y cifras: [`data/README.md`](data/README.md).
- **Uso en este proyecto:** análisis exploratorio, preparación de datos y construcción/evaluación de un modelo predictivo de rendimiento académico.

Antes de iniciar el análisis, se debe descargar el dataset desde Kaggle y verificar el nombre del archivo, las columnas, el diccionario de datos, la licencia y las condiciones de uso. La estructura exacta debe confirmarse sobre el archivo descargado, ya que puede cambiar entre versiones.

## 3. Problema de negocio

La institución educativa necesita decidir cómo distribuir sus recursos limitados de acompañamiento académico. Si espera hasta el cierre del periodo para identificar dificultades, puede perder la oportunidad de intervenir a tiempo. Por otro lado, ofrecer apoyo intensivo a todos los estudiantes sin priorización puede resultar costoso y poco eficiente.

Se plantea desarrollar un modelo que estime el rendimiento o identifique estudiantes que podrían requerir apoyo, utilizando las variables académicas y contextuales disponibles en el conjunto de datos. Los resultados servirán para priorizar una revisión por parte de docentes, orientadores y coordinadores académicos.

## 4. Objetivo general

Construir y evaluar un modelo de Machine Learning que utilice la información del dataset para apoyar la identificación temprana de estudiantes con posible riesgo de bajo rendimiento académico y orientar la asignación de acciones de acompañamiento.

## 5. Objetivos específicos

- Explorar la estructura, calidad y distribución de los datos.
- Identificar valores faltantes, duplicados, inconsistencias y posibles valores atípicos.
- Analizar la relación entre las variables disponibles y el resultado académico seleccionado.
- Preparar variables numéricas y categóricas para el entrenamiento.
- Comparar modelos adecuados para la tarea: por ejemplo, regresión si se predice una nota numérica, o clasificación si se predice una categoría de rendimiento o aprobación.
- Evaluar el desempeño del modelo con métricas apropiadas para el problema.
- Traducir los resultados a una recomendación de negocio comprensible para el equipo académico.
- Revisar posibles sesgos y evitar que las variables sensibles o contextuales se utilicen de manera injusta.

## 6. Decisión de negocio: las cuatro preguntas

### 6.1 ¿Quién decide?

**Responsable propuesto:** director(a) académico(a) o coordinador(a) académico(a) de la institución educativa.

Este cargo es responsable de revisar los indicadores de rendimiento, coordinar las acciones pedagógicas y decidir cómo distribuir recursos de acompañamiento. Los docentes y orientadores pueden aportar contexto y validar cada caso. El cargo indicado es una propuesta para el caso académico, no una persona real identificada en el dataset.

### 6.2 ¿Qué decide?

**Acción concreta:** determinar qué estudiantes deben ser priorizados para una revisión académica y, cuando corresponda, ofrecerles tutorías, refuerzo en asignaturas o acompañamiento adicional antes de la evaluación final.

El modelo no debe decidir automáticamente que un estudiante fracasa ni imponer consecuencias. Su resultado funciona como una alerta para que el equipo académico revise el caso y determine la intervención adecuada.

### 6.3 ¿Con qué información decide?

**Fuente principal:** el dataset [Student Exam Performance & Success Dataset de Kaggle](https://www.kaggle.com/datasets/mobeenfatimah/student-exam-performance-and-success-dataset).

Las variables disponibles en el archivo (44 columnas) se agrupan así; el detalle está en [`data/README.md`](data/README.md):

- **Historial académico:** `previous_exam_score`, `previous_gpa`, `attendance_percentage`, `assignment_completion_rate`, `class_participation`.
- **Hábitos de estudio:** `study_hours_per_day`, `self_study_hours`, `online_learning_hours`, `study_consistency`, `study_method`, `revision_frequency`, `practice_tests_completed`, `notes_quality`, `study_environment`, `private_tuition`, `exam_preparation_days`.
- **Bienestar y recursos:** `sleep_hours`, `sleep_quality`, `stress_level`, `motivation_level`, `daily_screen_time`, `physical_activity_hours`, `break_frequency`, `internet_access`, `device_availability`, `educational_app_usage`, `online_course_hours`.
- **Contexto (sensible):** `age`, `gender`, `school_type`, `family_income`, `parent_education`, `urban_rural`; además `education_level`.
- **Alrededor del examen (a revisar):** `exam_difficulty`, `time_management_score`, `exam_anxiety_level`.
- **Resultado del examen (no se usan para predecir):** `exam_score`, `pass_status` (corte en 50), `performance_grade`, `performance_level`, `questions_correct`, `questions_attempted`.

**Regla de aprobación:** el estudiante **aprueba con 70 o más** y **pierde el curso con menos de 70** (69 pierde).

**Variable objetivo:** `pass_70` (`Pass` 30,8 % / `Fail` 69,2 %), con `Fail` como clase de interés. Es un problema de **clasificación**: la acción (dar apoyo o no) es de sí/no. `pass_70` se deriva de `exam_score` (`Pass` si ≥ 70), por lo que la nota queda fuera de los predictores. La columna `pass_status` del dataset usa el corte de 50: **no es el objetivo** y también se excluye. `exam_score` (0–100) queda como alternativa de regresión si el grupo prefiere estimar la nota.

**Partición:** `student_id` es único (100.000 ids para 100.000 filas), así que no hay estudiantes repetidos y se parte por fila, estratificado por `pass_70`.

No se deben utilizar como variables predictoras datos que solo se conocen después de la decisión que se quiere anticipar, porque provocarían fuga de información (*data leakage*).

### 6.4 ¿Cuánto cuesta equivocarse? ¿Cuesta lo mismo en ambas direcciones?

**No. El costo puede ser diferente según el tipo de error.** Para este caso se deben distinguir, al menos, dos escenarios:

- **Falso positivo:** el modelo señala que un estudiante está en riesgo, pero en realidad no lo está. La institución podría invertir tiempo y dinero en una tutoría que quizá no era necesaria, y el estudiante podría experimentar una preocupación innecesaria. Aun así, una intervención de bajo costo puede ser aceptable si también beneficia al estudiante.
- **Falso negativo:** el modelo indica que un estudiante no está en riesgo, pero sí necesita apoyo. La institución podría no intervenir a tiempo, lo que puede contribuir a una calificación baja, pérdida de una asignatura, retraso académico o mayor necesidad de recuperación posterior.

En general, un falso negativo podría tener un costo académico y humano mayor que un falso positivo, aunque esto depende del contexto y del costo de las intervenciones. Por eso no basta con maximizar la exactitud (*accuracy*): conviene evaluar la sensibilidad (*recall*) para detectar estudiantes en riesgo, la precisión (*precision*) para controlar las alertas innecesarias y la matriz de confusión. Los umbrales de decisión deben acordarse con el equipo académico y considerar la capacidad real de atención.

Una forma sencilla de representar el costo esperado es:

**Costo esperado = (número de falsos positivos × costo por falso positivo) + (número de falsos negativos × costo por falso negativo).**

Los costos deben estimarse con la institución; no se pueden deducir únicamente del dataset.

## 7. Enfoque de trabajo

1. **Descarga y revisión:** obtener el archivo de Kaggle, revisar su licencia, columnas, tipos de datos y significado de las variables.
2. **Análisis exploratorio (EDA):** estudiar distribuciones, datos faltantes, valores extremos y relaciones entre variables.
3. **Preparación:** limpiar los datos, tratar valores faltantes, codificar variables categóricas y separar entrenamiento y prueba.
4. **Línea base:** crear un modelo sencillo para contar con una referencia de comparación.
5. **Entrenamiento:** comparar modelos apropiados para clasificación o regresión según la variable objetivo.
6. **Evaluación:** utilizar métricas pertinentes y revisar especialmente los errores que puedan dejar sin apoyo a estudiantes que lo necesitan.
7. **Interpretación:** comunicar qué variables se asocian con las predicciones, sin confundir asociación con causalidad.
8. **Recomendación:** proponer un flujo de revisión humana y seguimiento de las intervenciones.
9. **Monitoreo:** comprobar periódicamente si el modelo mantiene su desempeño y si sus errores afectan de forma desigual a distintos grupos.

## 8. Métricas de evaluación

La selección final depende del objetivo:

- **Clasificación:** matriz de confusión, *recall*, *precision*, F1 y, cuando sea apropiado, ROC-AUC o PR-AUC.
- **Regresión:** MAE, RMSE y R².
- **Perspectiva de negocio:** número de estudiantes correctamente identificados, volumen de alertas, capacidad de atención y costo estimado de los errores.

Las métricas deben calcularse sobre datos no utilizados para entrenar el modelo. Si existe una dimensión temporal, se debe considerar una separación que evite usar información futura para predecir el pasado.

## 9. Consideraciones éticas y limitaciones

- Una predicción es una estimación y no una certeza sobre el futuro del estudiante.
- No utilizar la predicción como única base para decisiones de alto impacto.
- Proteger los datos personales y limitar su acceso al personal autorizado.
- Evaluar si el desempeño del modelo varía entre grupos y si alguna variable actúa como sustituto de una característica sensible.
- No asumir que una correlación demuestra que una variable causa el rendimiento.
- Documentar los supuestos, las limitaciones, las métricas y la versión de los datos y del modelo.
- Confirmar la licencia y las condiciones de uso del dataset antes de redistribuirlo o utilizarlo fuera del ejercicio académico.

## 10. Estructura sugerida del repositorio

Estructura obligatoria del curso (detalle en `CLAUDE.md`):

```text
├── data/
│   ├── README.md                       # Diccionario de variables y cifras del dataset
│   ├── student_exam_performance.csv    # Datos originales (nunca se modifican)
│   ├── raw/  processed/                # processed/ guarda train y test
├── notebooks/                          # 01_caso_negocio … 09_inferencia
├── src/proyecto/                       # data/ features/ models/ tracking/ inference/
├── tests/
├── models/                             # model.joblib + ficha_modelo.md
├── app/streamlit_app.py
├── reports/                            # 00_caso … 09_despliegue + informe_tecnico.md
├── especificaciones/                   # 02-eda.md, 03-preprocesamiento.md
├── especificacion-proyecto.md          # Caso, objetivo, métrica y decisiones
├── presentacion/ejecutiva.md
├── requirements.txt  .env.example  .gitignore  README.md  CLAUDE.md
```

Se recomienda no subir al repositorio datos personales o archivos cuya licencia no permita su redistribución. Si el CSV es voluminoso o tiene restricciones, incluir instrucciones para descargarlo desde Kaggle en lugar de versionarlo.

## 11. Resultado esperado

Un prototipo analítico que permita estimar el rendimiento o detectar posibles señales de riesgo académico, presentar resultados interpretables y apoyar al equipo académico en la priorización de intervenciones. El éxito no se medirá solo por el desempeño estadístico, sino también por la utilidad de las alertas, el costo de los errores, la equidad y la capacidad de la institución para actuar sobre ellas.

## 12. Referencia

Fatimah, M. (s. f.). *Student Exam Performance & Success Dataset*. Kaggle.  
https://www.kaggle.com/datasets/mobeenfatimah/student-exam-performance-and-success-dataset
