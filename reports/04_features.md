# Informe de variables

> Resultado de `notebooks/04b_features_aprueba_o_no.ipynb` (plantilla del curso: `04_features.ipynb`; ejemplo: `material-del-curso/ejemplo-creditsight/notebooks/04_features.ipynb`).
> Cada idea de variable es una **hipótesis medida** con la misma validación; se conserva solo si la mejora supera el ruido entre pliegues.
> Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 1. Tabla completa: `reports/04_features_tabla.csv`.
> **Estado:** medido por Claude con el CSV real; las decisiones son **propuestas** hasta que el grupo las apruebe y la institución confirme los supuestos marcados.

## Cómo se midió

> Contexto fijo del caso (`data/README.md`): objetivo `pass_70` (aprueba con 70 o más), clase de interés `Fail` (69,2 %); **no se pueden usar** `exam_score`, `pass_status` (corte en 50), `performance_grade`, `performance_level`, `questions_correct` ni `questions_attempted`.

- **Modelo (parámetros fijos):** LightGBM, 300 árboles, `learning_rate` 0,05, 31 hojas, semilla 42. No se busca el mejor modelo (eso es la etapa 5), solo se compara el conjunto de variables.
- **Métrica principal** (y por qué): costo esperado por estudiante (falso negativo = 5, falso positivo = 1; **supuesto a validar con la institución**), con *recall* de `Fail` y NPV. Se avisa si P(Fail) ≥ 0,167. La referencia a vencer es «avisar a todos»: costo **0,308** en estos pliegues.
- **Métricas de control:** *recall* y precisión de `Fail`, NPV (hace falta > 83,3 %), alertas por 100, PR-AUC de `Fail` y *log loss* (calidad de las probabilidades).
- **Pliegues** (cuántos y partidos por qué entidad): 5, **por fila** y estratificados por `pass_70` (`student_id` es único: no hay entidades repetidas), con los 80.000 estudiantes de entrenamiento; semilla 42. Los mismos para todas las variantes. La prueba (`test.joblib`) no se abrió.
- **Regla de decisión escrita antes de medir:** (a) *añadir* una variable: se conserva si mejora / ruido > 1 y se conoce al predecir; (b) *quitar* columnas: se quitan si el costo no empeora más que el ruido (mejora / ruido > −1), porque a igual desempeño conviene tener menos columnas; (c) *con y sin*: si quitarlas empeora por mucho más que el ruido, la variable aporta y la decisión pasa a ser un supuesto de negocio (cuándo se mide).

## Tabla de ideas medidas

> La fila 0 es la **referencia** (las 35 variables de la etapa 3, con indicador de vacío). «Mejora / ruido» = mejora de costo dividida por su desviación entre pliegues; menor que ~1 está dentro del ruido. Costo de la referencia: **0,2579 ± 0,0048**.

| # | Idea (variable y cómo se calcula) | ¿Se conoce al predecir? | Costo (± ruido) | Mejora / ruido | Decisión (propuesta) |
|---|---|---|---|---|---|
| 0 | **Referencia** (35 variables) | — | 0,2579 ± 0,0048 | 0 | — |
| 1 | `self_study_share` = `self_study_hours` / `study_hours_per_day` *(no se suman las horas: `self_study_hours` es una parte de `study_hours_per_day` en el 100 % de las filas)* | ☑ sí | 0,2581 ± 0,0032 | −0,07 | ☑ descartar |
| 2 | `prep_total_hours` = `study_hours_per_day` × `exam_preparation_days` | ☑ sí | 0,2591 ± 0,0043 | −0,29 | ☑ descartar |
| 3 | Sin indicador de vacío (0/1) | ☑ sí | 0,2581 ± 0,0047 | −0,04 | ☑ quitar |
| 4 | Sin `exam_difficulty` | ☐ **por confirmar** | 0,2828 ± 0,0017 | −14,6 | ☑ conservar la variable (condicionada) |
| 5 | Sin `time_management_score` ni `exam_anxiety_level` | ☐ **por confirmar** | 0,2570 ± 0,0023 | +0,36 | ☐ no concluyente: conservar por ahora |
| 6 | Sin las 3 de «con y sin» | ☑ (peor caso) | 0,2815 ± 0,0025 | −9,4 | — (referencia del peor caso) |
| 7 | Sin las 7 columnas sin señal (`age`, `internet_access`, `private_tuition`, `daily_screen_time`, `physical_activity_hours`, `online_learning_hours`, `online_course_hours`) | ☑ sí | 0,2577 ± 0,0036 | +0,04 | ☑ quitar |
| 8 | **Propuesta final** = ideas 3 + 7 juntas | ☑ sí | 0,2584 ± 0,0030 | −0,18 | ☑ es la propuesta |

Todas las variantes con modelo superan a «avisar a todos» (0,308): NPV entre 90,2 % y 92,2 %, frente al mínimo de 83,3 %.

## Decisiones y motivos

- **`self_study_share`: descartar.** Mejora / ruido −0,07; la variable ni separa las clases (mediana 0,700 en `Fail` frente a 0,698 en `Pass`).
- **`prep_total_hours`: descartar.** Mejora / ruido −0,29 y gana en 1 de 5 pliegues. Se ve distinta a simple vista (mediana 29 h en `Fail` y 53 h en `Pass`), pero no mejora el costo: ver diferencia no es mejorar el modelo.
- **Indicador de vacío: quitar.** −0,04 veces el ruido; coherente con el EDA, donde estar vacío no se asocia con perder el curso (`Fail` 68,3–69,4 % frente a 69,2 %).
- **`exam_difficulty`: conservar, con una condición.** Sin ella el costo sube de 0,258 a 0,283 (9 a 15 veces el ruido; pierde en los 5 pliegues) y el *log loss* de 0,370 a 0,425: **el modelo pierde la mitad de su ventaja sobre «avisar a todos»** (de 0,050 a 0,025 por estudiante).
- **`time_management_score` y `exam_anxiety_level`: no concluyente.** Con `exam_difficulty` presente, quitarlas deja el costo igual (0,257 frente a 0,258) y el *log loss* apenas peor (1,2 veces el ruido). Se conservan por ahora; si no se conocen al avisar, se pueden quitar sin perder costo.
- **7 columnas sin señal: quitar** (costo igual; la app pide 7 datos menos; sale `age`, que incluye menores). **Juntas** con la idea 3 (variante 8): 0,2584 frente a 0,2579, dentro del ruido.

## Supuestos y riesgos

- **Supuesto de negocio (el más importante):** `exam_difficulty` (y, en menor medida, `time_management_score` y `exam_anxiety_level`) solo valen si se **conocen en el momento de avisar** al estudiante. Si se conocen después, usarlas sería una fuga y el costo real sería el de la variante 6 (≈ 0,28; ventaja de 0,026 sobre «avisar a todos»). **Confirmarlo con la institución antes de la etapa 5.**
- **El modelo avisa a ~90 de cada 100 estudiantes** con el umbral de 0,167 (consecuencia del supuesto 5 a 1). Si la institución solo puede atender a una parte, esa regla no es utilizable tal cual; se aborda en la etapa 5 con la capacidad real. El PR-AUC de 0,95 (frente a 0,69 del azar) muestra que el modelo ordena bien; falta medir qué pasa al avisar solo a los más riesgosos.
- **Los costos 5 a 1 no salen de los datos:** si cambian, cambian el umbral y la comparación.
- **Ruido estimado con 5 pliegues:** es una estimación gruesa; las diferencias menores que ~1 desviación no se deben interpretar.
- **Sensibles:** `gender` y `family_income` siguen fuera de las variables. `age` sale del modelo por no aportar. La auditoría por grupo es de la etapa 7.

## Qué se lleva el pipeline final

- **28 variables** (12 numéricas + 16 categóricas) = las 35 de la etapa 3 menos las 7 sin señal; **sin indicador de vacío**; **sin variables nuevas**.
- **Imputación** dentro del `Pipeline` (mediana en numéricas; «Desconocido» en categóricas), ajustada solo con entrenamiento.
- **Código:** `src/proyecto/features/engineering.py` (`feature_columns`, `build_preprocessor`, `add_features`, `STAGE4_DROP`, `STAGE4_ADD_MISSING_INDICATOR`), `src/proyecto/models/train.py` (`build_pipeline`, `business_metrics`, `evaluate_folds`) y `src/proyecto/data/split.py` (`make_folds`). Pruebas: `tests/test_features.py`, `tests/test_train.py`, `tests/test_split.py`.
- **Pendiente de aprobación del grupo** (casillas del notebook 04b sin marcar).
