# Informe del torneo de modelos

> Resultado de `notebooks/05b_torneo_aprueba_o_no.ipynb` (plantilla del curso: `05_torneo.ipynb`; ejemplo: `material-del-curso/ejemplo-creditsight/notebooks/05_torneo.ipynb`).
> El torneo **descarta**: elige 1–2 finalistas con evidencia, no un campeón definitivo. Guía:
> `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 2.
> **Estado:** medido por Claude con el CSV real (solo entrenamiento; la prueba no se abrió). Las decisiones son **propuestas** hasta que el grupo las apruebe. Tablas completas: `reports/05_torneo_tabla.csv`, `05_torneo_tecnicas.csv`, `05_torneo_capacidad.csv` y `05_torneo_peor_caso.csv`.

## Reglas del torneo

- **Mismos datos y mismos pliegues para todos** (partidos por qué entidad): 5 pliegues por fila, estratificados por `pass_70`, semilla 42 (los mismos de la etapa 4); `student_id` es único, no hay entidades repetidas.
- **Línea base** (qué es y cuánto da): `DummyClassifier` que predice la tasa de `Fail`; con el umbral de 0,167 equivale a **«avisar a todos»**: costo **0,308** por estudiante, ROC-AUC 0,5, PR-AUC 0,692, *recall* de `Fail` 100 %, especificidad 0. Un modelo la supera solo con NPV > 83,3 %.
- **Métrica principal** (la del negocio) y **métricas técnicas** que reportas: principal = costo por estudiante (5 : 1, **supuesto a validar con la institución**; se avisa si P(`Fail`) ≥ 0,167), *recall* de `Fail` y NPV; técnicas = ROC-AUC, PR-AUC, exactitud balanceada, precisión, *recall* y especificidad, F1 y *log loss*; clase de interés = `Fail` (69,2 %).
- **Variables usadas** (las decididas en `reports/04_features.md`): propuesta de la etapa 4 = 28 variables (`feature_columns(drop=STAGE4_DROP)`), sin indicador de vacío y sin variables nuevas; `exam_difficulty` incluida **si la institución confirma que se conoce al avisar** (si no: sin las 3 de «con y sin»; ver «Peor caso»).
- **Regla de decisión escrita antes de correr:** un modelo que no supera a «avisar a todos» queda fuera; los empatados (diferencia / ruido < 1 y sin ganar en todos los pliegues) se desempatan por simplicidad e interpretabilidad y luego por tiempo; máximo 2 finalistas.

## Tabla comparativa

> Media ± desviación entre pliegues. Ordenada por la métrica principal (menor es mejor).

| Modelo | Costo por estudiante (± ruido) | NPV | Alertas por 100 | Segundos de ajuste |
|---|---|---|---|---|
| Regresión logística | 0,2576 ± 0,0032 | 91,7 % | 90,0 | 0,6 |
| XGBoost | 0,2583 ± 0,0034 | 91,7 % | 90,0 | 1,2 |
| LightGBM | 0,2584 ± 0,0030 | 91,7 % | 90,1 | 0,9 |
| Random forest | 0,2827 ± 0,0010 | 97,7 % | 97,1 | 4,2 |
| Línea base (avisar a todos) | 0,3079 ± 0,0000 | no existe | 100 | 0,2 |

## Métricas técnicas

> Media entre pliegues, con la misma validación. Las de ranking (ROC-AUC, PR-AUC) usan las probabilidades; las de clasificación usan la decisión de negocio (umbral 0,167).

| Modelo | ROC-AUC | PR-AUC `Fail` | Exactitud balanceada | Precisión `Fail` | *Recall* `Fail` | Especificidad (*recall* `Pass`) | F1 `Fail` | *Log loss* |
|---|---|---|---|---|---|---|---|---|
| Regresión logística | 0,892 | 0,949 | 0,643 | 0,760 | 0,988 | 0,299 | 0,859 | 0,373 |
| XGBoost | 0,894 | 0,950 | 0,642 | 0,759 | 0,988 | 0,296 | 0,859 | 0,370 |
| LightGBM | 0,894 | 0,950 | 0,641 | 0,759 | 0,988 | 0,295 | 0,859 | 0,370 |
| Random forest | 0,885 | 0,944 | 0,546 | 0,712 | 0,999 | 0,093 | 0,832 | 0,400 |
| Línea base | 0,500 | 0,692 | 0,500 | 0,692 | 1,000 | 0,000 | 0,818 | 0,617 |

## ¿Coinciden los rankings de negocio y técnico?

> Posición de cada modelo (1 = mejor).

| Modelo | Negocio (costo) | ROC-AUC | F1 `Fail` | *Recall* `Fail` | Especificidad |
|---|---|---|---|---|---|
| Regresión logística | 1 | 3 | 1 | 5 | 1 |
| XGBoost | 2 | 2 | 2 | 4 | 2 |
| LightGBM | 3 | 1 | 3 | 3 | 3 |
| Random forest | 4 | 4 | 4 | 2 | 4 |

- **¿El mejor por la métrica de negocio también es el mejor por AUC?** No (regresión logística frente a LightGBM), pero la diferencia de ROC-AUC es de 0,002: es el mismo empate visto con otra métrica.
- **¿Hay modelos con AUC casi igual pero costo distinto? ¿Por qué?** Sí: random forest (0,885) frente a los otros (0,892–0,894) tiene un AUC cercano pero un costo 0,025 mayor. Decide con **probabilidades peor calibradas**: con el umbral de 0,167 avisa a 97 de cada 100. Con la regla de la «clase más probable» (0,5) es el de menor costo entre los modelos (0,392 frente a 0,437).
- **¿Hay alguna clase con *recall* casi nulo en algún modelo? ¿Cuál y qué le cuesta al negocio?** `Pass`: la especificidad es de 0,30 en tres modelos y de **0,09 en random forest**. Siete a diez de cada 10 estudiantes que aprobarían reciben aviso; se pierde la capacidad de discriminar y se satura la tutoría. La exactitud simple (0,78) lo esconde.

## Comparación pareada de los mejores

> Todos se evaluaron en los mismos pliegues: ¿gana siempre el mismo?

| Mejor | Contra | Diferencia media | Pliegues que gana | Diferencia / ruido |
|---|---|---|---|---|
| Regresión logística | XGBoost | 0,0006 | 3 de 5 | 0,16 |
| Regresión logística | LightGBM | 0,0008 | 3 de 5 | 0,20 |
| XGBoost | LightGBM | 0,0001 | 2 de 5 | 0,10 |
| Regresión logística | Random forest | 0,0250 | 5 de 5 | 7,9 |
| LightGBM | Random forest | 0,0243 | 5 de 5 | 8,5 |

## ¿Cuánto vale la diferencia?

- **Decisiones estimadas por periodo:** **dato que la institución debe definir**. Como ilustración se usa el tamaño del dataset: 100.000 estudiantes (no es una estimación de la institución). Costos en unidades relativas (1 = una tutoría que no hacía falta).
- **Ahorro frente a la línea base** (por 100.000 estudiantes): regresión logística ≈ 5.026 unidades, XGBoost ≈ 4.962, LightGBM ≈ 4.950, random forest ≈ 2.524.
- **Diferencia entre el mejor y el siguiente:** 64 a 76 unidades (LightGBM y XGBoost frente a la logística): un empate práctico. Random forest cuesta ≈ 2.500 unidades más.

## Finalistas

| Finalista | Por qué (consistencia, métrica, tiempo, interpretabilidad) | Qué podría cambiar con la optimización |
|---|---|---|
| **Regresión logística** | Menor costo (0,2576); la más rápida (0,6 s); **explicable** (cada variable tiene un peso) | Poco: casi sin parámetros que afinar; es la referencia a batir |
| **LightGBM** | Mejor ROC-AUC (0,894), PR-AUC (0,950) y *log loss* (0,370); primero en el peor caso (0,2815) | Hiperparámetros y umbral; si no supera a la logística tras optimizar, se queda la logística |

**Modelos descartados y por qué:** random forest (pierde en los 5 pliegues contra cualquiera de los otros tres, 7,4 a 8,5 veces el ruido; ahorra la mitad; el más lento) y XGBoost (empata con LightGBM, 0,1 veces el ruido, y es más lento: misma familia).

**Por qué el torneo no elige un campeón** (con tus palabras): tres modelos empatan en costo y ordenan igual de bien; elegir uno de ellos hoy sería escoger entre ruidos. La optimización puede cambiar el orden y solo la prueba final (etapa 7) dice qué tan bueno es el modelo elegido.

## Efectos que la métrica principal no ve

- **El aviso casi no discrimina con el costo 5 : 1:** el modelo avisa a ≈ 90 de cada 100 y deja tranquilo solo al 30 % de quienes aprobarían (especificidad 0,30). La métrica de costo se ve bien, pero la tutoría se saturaría.
- **Capacidad limitada (`05_torneo_capacidad.csv`):** si solo se puede avisar al 30 % más riesgoso, la regresión logística acierta el 98,3 % de sus alertas (el azar, 68,9 %) y detecta el 42,6 % de quienes pierden el curso, de un máximo posible de 43,3 %. Pero el costo sube a 1,99 (frente a 0,308 de avisar a todos), porque cada estudiante en riesgo sin aviso cuesta 5. Con cupo limitado, **el costo 5 : 1 deja de ser la métrica adecuada**; la institución debe definir su capacidad (`MAX_ALERTS_PER_100`) o el costo real.
- **Peor caso (sin `exam_difficulty`, `time_management_score` y `exam_anxiety_level`):** todos los modelos empeoran (logística 0,2576 → 0,2816; LightGBM 0,2584 → 0,2815) y la ventaja sobre «avisar a todos» se reduce a la mitad (≈ 0,050 → ≈ 0,026). Los tres primeros siguen empatados (LightGBM 0,2815, logística 0,2816, XGBoost 0,2828) y random forest sigue último (0,2959): **la elección de finalistas no depende del supuesto; el valor del modelo sí.**
- **Calibración y umbral:** el umbral de 0,167 supone probabilidades bien calibradas; random forest, en particular, no lo está. Se ajusta con validación en la etapa 6 y la calibración se evalúa en la etapa 7, sin usar la prueba.
- **Supuestos abiertos:** costos 5 : 1; cuándo se conoce `exam_difficulty`; volumen de estudiantes por periodo.
