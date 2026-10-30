# Predicción del rendimiento y éxito académico de estudiantes

## 1. Descripción del proyecto

Este proyecto propone utilizar técnicas de análisis de datos y *Machine Learning* para apoyar la toma de decisiones en una institución educativa. El propósito es identificar estudiantes que podrían presentar bajo rendimiento académico o riesgo de no alcanzar los resultados esperados, para que el equipo académico pueda evaluar intervenciones oportunas, como tutorías, acompañamiento o refuerzos.

El modelo debe utilizarse como una herramienta de apoyo y no como un mecanismo automático para sancionar, excluir o limitar oportunidades educativas.

## 2. Fuente de datos

- **Dataset:** [Student Exam Performance & Success Dataset — Kaggle](https://www.kaggle.com/datasets/mobeenfatimah/student-exam-performance-and-success-dataset)
- **Autor en Kaggle:** Mobeen Fatimah.
- **Formato esperado:** archivo(s) CSV descargados desde Kaggle.
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

Se utilizarán las variables que realmente estén disponibles en el archivo descargado. Dependiendo del esquema, podrían incluir resultados de exámenes anteriores, calificaciones, asistencia, hábitos de estudio y características educativas o contextuales. Estas variables son ejemplos posibles y deben confirmarse contra las columnas reales del dataset.

La variable objetivo también debe definirse de acuerdo con los datos disponibles:
- **Clasificación:** predecir una categoría, por ejemplo, riesgo/no riesgo o aprobado/no aprobado, siempre que exista una etiqueta adecuada.
- **Regresión:** estimar una calificación numérica, si el conjunto de datos contiene una nota como objetivo.

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

```text
student-exam-performance/
├── data/
│   └── README.md              # Instrucciones para obtener los datos
├── notebooks/
│   └── 01_analisis_exploratorio.ipynb
├── src/
│   ├── preprocessing.py
│   └── train_model.py
├── reports/
│   └── figures/
├── requirements.txt
├── .gitignore
└── README.md
```

Se recomienda no subir al repositorio datos personales o archivos cuya licencia no permita su redistribución. Si el CSV es voluminoso o tiene restricciones, incluir instrucciones para descargarlo desde Kaggle en lugar de versionarlo.

## 11. Resultado esperado

Un prototipo analítico que permita estimar el rendimiento o detectar posibles señales de riesgo académico, presentar resultados interpretables y apoyar al equipo académico en la priorización de intervenciones. El éxito no se medirá solo por el desempeño estadístico, sino también por la utilidad de las alertas, el costo de los errores, la equidad y la capacidad de la institución para actuar sobre ellas.

## 12. Referencia

Fatimah, M. (s. f.). *Student Exam Performance & Success Dataset*. Kaggle.  
https://www.kaggle.com/datasets/mobeenfatimah/student-exam-performance-and-success-dataset
