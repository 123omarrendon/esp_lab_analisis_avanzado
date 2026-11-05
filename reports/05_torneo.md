# Informe del torneo de modelos

> Resultado de `notebooks/05b_torneo_aprueba_o_no.ipynb` (plantilla del curso: `05_torneo.ipynb`; ejemplo: `material-del-curso/ejemplo-creditsight/notebooks/05_torneo.ipynb`).
> El torneo **elige al modelo ganador para seguir adelante**, no lo corona: la optimización puede cambiar el orden y solo la prueba final lo confirma. Guía:
> `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 2.
> **Estado:** medido con el CSV real (solo entrenamiento; la prueba no se abrió). La decisión es una **propuesta** hasta que el grupo la apruebe. Tablas completas: `reports/05_torneo_tabla.csv`, `05_torneo_tecnicas.csv`, `05_torneo_capacidad.csv` y `05_torneo_peor_caso.csv`.

## Reglas del torneo

- **Mismos datos y mismos pliegues para todos** (partidos por qué entidad): 5 pliegues por fila, estratificados por `pass_70`, semilla 42 (los mismos de la etapa 4); `student_id` es único, no hay entidades repetidas.
- **Referencias sin modelo** (qué son y cuánto dan): `DummyClassifier` (línea base) y `DummyRegressor` (media), que predicen la tasa de `Fail` (69,2 %) para todos. Con el umbral de 0,167 equivalen a **«avisar a todos»**: costo **0,308** por estudiante, ROC-AUC 0,5, PR-AUC 0,692, *recall* de `Fail` 100 %, especificidad 0. Un modelo las supera solo con NPV > 83,3 %. **No compiten por ganar.**
- **Candidatos:** regresión logística, **KNN (5 vecinos, `n_neighbors=5`)**, random forest, LightGBM y XGBoost.
- **Métrica principal** (la del negocio) y **métricas técnicas** que reportas: principal = costo por estudiante (5 : 1, **supuesto a validar con la institución**; se avisa si P(`Fail`) ≥ 0,167), *recall* de `Fail` y NPV; técnicas = ROC-AUC, PR-AUC, exactitud balanceada, precisión, *recall* y especificidad, F1 y *log loss*; clase de interés = `Fail` (69,2 %).
- **Variables usadas** (las decididas en `reports/04_features.md`): propuesta de la etapa 4 = 28 variables (`feature_columns(drop=STAGE4_DROP)`), sin indicador de vacío y sin variables nuevas; `exam_difficulty` incluida **si la institución confirma que se conoce al avisar** (si no: sin las 3 de «con y sin»; ver «Peor caso»).
- **Regla de decisión escrita antes de correr:** un modelo que no supera a «avisar a todos» queda fuera; gana **un solo modelo**, el de menor costo; si hay empate (diferencia / ruido < 1 y sin ganar en todos los pliegues) gana el más simple e interpretable y luego el más rápido.

## Tabla comparativa

> Media ± desviación entre pliegues. Ordenada por la métrica principal (menor es mejor). Los segundos de ajuste varían según el equipo.

| Modelo | Costo por estudiante (± ruido) | NPV | Alertas por 100 | Segundos de ajuste |
|---|---|---|---|---|
| **Regresión logística** | **0,2576 ± 0,0032** | 91,7 % | 90,0 | ≈ 0,7 |
| XGBoost | 0,2583 ± 0,0034 | 91,7 % | 90,0 | ≈ 1,2 |
| LightGBM | 0,2584 ± 0,0030 | 91,7 % | 90,1 | ≈ 0,9 |
| Random forest | 0,2827 ± 0,0010 | 97,7 % | 97,1 | ≈ 4 a 6 |
| KNN (5 vecinos) | 0,3006 ± 0,0017 | 86,9 % | 96,6 | < 1 (la espera está al predecir) |
| `DummyRegressor` (media) | 0,3079 ± 0,0000 | no existe | 100 | ≈ 0,3 |
| Línea base (avisar a todos) | 0,3079 ± 0,0000 | no existe | 100 | ≈ 0,2 |

## Métricas técnicas

> Media entre pliegues, con la misma validación. Las de ranking (ROC-AUC, PR-AUC) usan las probabilidades; las de clasificación usan la decisión de negocio (umbral 0,167).

| Modelo | ROC-AUC | PR-AUC `Fail` | Exactitud balanceada | Precisión `Fail` | *Recall* `Fail` | Especificidad (*recall* `Pass`) | F1 `Fail` | *Log loss* |
|---|---|---|---|---|---|---|---|---|
| Regresión logística | 0,892 | 0,949 | 0,643 | 0,760 | 0,988 | 0,299 | 0,859 | 0,373 |
| XGBoost | 0,894 | 0,950 | 0,642 | 0,759 | 0,988 | 0,296 | 0,859 | 0,370 |
| LightGBM | 0,894 | 0,950 | 0,641 | 0,759 | 0,988 | 0,295 | 0,859 | 0,370 |
| Random forest | 0,885 | 0,944 | 0,546 | 0,712 | 0,999 | 0,093 | 0,832 | 0,400 |
| KNN (5 vecinos) | 0,793 | 0,862 | 0,545 | 0,712 | 0,994 | 0,097 | 0,830 | 1,456 |
| `DummyRegressor` y línea base | 0,500 | 0,692 | 0,500 | 0,692 | 1,000 | 0,000 | 0,818 | 0,617 |

## ¿Coinciden los rankings de negocio y técnico?

> Posición de cada modelo (1 = mejor).

| Modelo | Negocio (costo) | ROC-AUC | F1 `Fail` | *Recall* `Fail` | Especificidad |
|---|---|---|---|---|---|
| Regresión logística | 1 | 3 | 1 | 7 | 1 |
| XGBoost | 2 | 2 | 2 | 6 | 2 |
| LightGBM | 3 | 1 | 3 | 5 | 3 |
| Random forest | 4 | 4 | 4 | 3 | 5 |
| KNN (5 vecinos) | 5 | 5 | 5 | 4 | 4 |
| `DummyRegressor` y línea base | 6 | 6 | 6 | 1 | 6 |

- **¿El mejor por la métrica de negocio también es el mejor por AUC?** No (regresión logística frente a LightGBM), pero la diferencia de ROC-AUC es de 0,002: es el mismo empate visto con otra métrica.
- **¿Hay modelos con AUC casi igual pero costo distinto? ¿Por qué?** Sí: random forest (0,885) frente a los tres primeros (0,892–0,894) tiene un AUC cercano pero un costo 0,025 mayor. Decide con **probabilidades peor calibradas**: con el umbral de 0,167 avisa a 97 de cada 100. Con la regla de la «clase más probable» (0,5) es el de menor costo entre los modelos (0,392 frente a 0,437 de la logística).
- **¿Hay alguna clase con *recall* casi nulo en algún modelo? ¿Cuál y qué le cuesta al negocio?** `Pass`: la especificidad es de 0,30 en tres modelos y de **0,09 a 0,10 en random forest y KNN**. De siete a diez de cada 10 estudiantes que aprobarían reciben aviso; se pierde la capacidad de discriminar y se satura la tutoría. La exactitud simple (0,78) lo esconde.
- **KNN:** su *log loss* (1,456) es el peor por mucho: con 5 vecinos solo da probabilidades 0, 0,2, 0,4… 1, y con el umbral de 0,167 basta un vecino que pierda para avisar.

## Comparación pareada de los mejores

> Todos se evaluaron en los mismos pliegues: ¿gana siempre el mismo?

| Mejor | Contra | Diferencia media | Pliegues que gana | Diferencia / ruido |
|---|---|---|---|---|
| Regresión logística | XGBoost | 0,0006 | 3 de 5 | 0,16 |
| Regresión logística | LightGBM | 0,0008 | 3 de 5 | 0,20 |
| Regresión logística | Random forest | 0,0250 | 5 de 5 | 7,9 |
| Regresión logística | KNN (5 vecinos) | 0,0429 | 5 de 5 | 12,9 |

`DummyRegressor` frente a la línea base: la diferencia de costo es **exactamente 0** en los 5 pliegues (un regresor constante no aporta nada).

## ¿Cuánto vale la diferencia?

- **Decisiones estimadas por periodo:** **dato que la institución debe definir**. Como ilustración se usa el tamaño del dataset: 100.000 estudiantes (no es una estimación de la institución). Costos en unidades relativas (1 = una tutoría que no hacía falta).
- **Ahorro frente a la línea base** (por 100.000 estudiantes): regresión logística ≈ 5.026 unidades, XGBoost ≈ 4.962, LightGBM ≈ 4.950, random forest ≈ 2.524, **KNN ≈ 732**, `DummyRegressor` 0.
- **Diferencia entre el mejor y el siguiente:** 64 a 76 unidades (XGBoost y LightGBM frente a la logística): un empate práctico. Random forest cuesta ≈ 2.500 unidades más y KNN ≈ 4.300.

## Modelo ganador

**Regresión logística.**

| Modelo ganador | Por qué (consistencia, métrica, tiempo, interpretabilidad) | Qué podría cambiar con la optimización |
|---|---|---|
| **Regresión logística** | Menor costo (0,2576); la más rápida; **explicable** (cada variable tiene un peso que se puede mostrar a un coordinador académico); mismo ordenamiento que los modelos de boosting | Poco: casi sin parámetros que afinar (la regularización). Lo que más importa es el umbral y la calibración |

**Cómo se aplicó la regla:** regresión logística, LightGBM y XGBoost **empatan** (0,1 a 0,2 veces el ruido; ninguna gana en todos los pliegues); se desempata por simplicidad e interpretabilidad. Su ventaja es **estadísticamente un empate**: se elige por simplicidad, no porque sea claramente mejor.

**Modelos descartados y por qué:**
- **KNN (5 vecinos):** pierde en los 5 pliegues (12,9 veces el ruido), probabilidades en escalones gruesos (*log loss* 1,456), especificidad 0,10, y sin las 3 variables de «con y sin» cuesta más que no hacer nada (0,3088).
- **Random forest:** pierde en los 5 pliegues (7,4 a 8,5 veces el ruido); ahorra la mitad; el más lento.
- **LightGBM y XGBoost:** empate con la logística y más complejos; entre ellos también empatan.
- **`DummyRegressor`:** idéntico a la línea base; es una referencia, no un candidato.

**Por qué el torneo no corona** (con tus palabras): tres modelos empatan en costo y ordenan igual de bien; la elección del ganador es de simplicidad. La optimización puede cambiar el orden y solo la prueba final (etapa 7) dice qué tan bueno es el modelo elegido.

## Efectos que la métrica principal no ve

- **El aviso casi no discrimina con el costo 5 : 1:** el modelo avisa a ≈ 90 de cada 100 y deja tranquilo solo al 30 % de quienes aprobarían (especificidad 0,30). La métrica de costo se ve bien, pero la tutoría se saturaría.
- **Capacidad limitada (`05_torneo_capacidad.csv`):** si solo se puede avisar al 30 % más riesgoso, la regresión logística acierta el 98,3 % de sus alertas (el azar, 68,9 %; KNN, 91,8 %) y detecta el 42,6 % de quienes pierden el curso, de un máximo posible de 43,3 %. Pero el costo sube a 1,99 (frente a 0,308 de avisar a todos), porque cada estudiante en riesgo sin aviso cuesta 5. Con cupo limitado, **el costo 5 : 1 deja de ser la métrica adecuada**; la institución debe definir su capacidad (`MAX_ALERTS_PER_100`) o el costo real.
- **Peor caso (sin `exam_difficulty`, `time_management_score` y `exam_anxiety_level`):** todos los modelos empeoran (logística 0,2576 → 0,2816; LightGBM 0,2584 → 0,2815) y la ventaja sobre «avisar a todos» se reduce a la mitad (≈ 0,050 → ≈ 0,026). Los tres primeros siguen empatados y **la elección del ganador no depende del supuesto; el valor del modelo sí.** KNN pasa a costar más que no hacer nada (0,3088).
- **Calibración y umbral:** el umbral de 0,167 supone probabilidades bien calibradas; random forest y KNN, en particular, no lo están. Se ajusta con validación en la etapa 6 y la calibración se evalúa en la etapa 7, sin usar la prueba.
- **Supuestos abiertos:** costos 5 : 1; cuándo se conoce `exam_difficulty`; volumen de estudiantes por periodo.
