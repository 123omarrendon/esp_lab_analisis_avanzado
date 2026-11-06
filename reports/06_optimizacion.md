# Informe de la optimización

> Resultado de `notebooks/06b_optimizacion_aprueba_o_no.ipynb` (plantilla del curso: `06_optimizacion.ipynb`; ejemplo: `material-del-curso/ejemplo-creditsight/notebooks/06_optimizacion.ipynb`).
> La mejor puntuación de una búsqueda es **optimista**: se comprueba en estudiantes que la búsqueda no vio. Guía:
> `material-del-curso/kit/guia-modelado-y-optimizacion.md`, secciones 3 y 4.
> **Estado:** medido con el CSV real (solo entrenamiento; la prueba no se abrió). La decisión es una **propuesta** hasta que el grupo la apruebe. Datos: `reports/06_best_params.json` y `reports/06_comprobacion.csv`. Código: `src/proyecto/models/tuning.py`.

## Diseño de la búsqueda

- **Finalista(s) optimizado(s):** el modelo ganador del torneo (`reports/05_torneo.md`): **regresión logística**, con las 28 variables de la etapa 4. Es **un solo modelo**, a diferencia del ejemplo CreditSight (dos finalistas).
- **Espacio de búsqueda** (parámetro → rango y por qué ese rango):

| Parámetro | Rango | Motivo |
|---|---|---|
| `C` (inversa de la regularización) | 0,001 a 100, escala logarítmica | Valor de partida `C = 1`. Más chico contiene los coeficientes; más grande casi no regulariza. Sus efectos se miden en órdenes de magnitud |
| `threshold` (umbral de decisión: se avisa si P(`Fail`) ≥ umbral) | 0,05 a 0,40 | Alrededor del teórico 1 / (1 + 5) = 0,167. No es un parámetro del modelo sino de la **decisión**; se ajusta con validación, nunca con la prueba |

  La regresión logística casi no tiene hiperparámetros, por eso el espacio es corto.
- **Métrica optimizada:** costo esperado por estudiante (la del torneo; 5 : 1, supuesto a validar con la institución).
- **Presupuesto** (ensayos por modelo, fijado antes de empezar) y **por qué ese número:** 25 ensayos. Cada uno cuesta ≈ 1 s y el espacio tiene solo 2 parámetros; más ensayos no cambiarían nada.
- **Estudiantes reservados** (qué porcentaje, partidos por qué entidad, semilla): 25 % del entrenamiento (20.000 estudiantes), **por fila** y estratificado por `pass_70` (cada fila es un estudiante distinto, `student_id` único); semilla 7. La búsqueda usa los otros 60.000 con validación cruzada de 3 pliegues (semilla 42). El intervalo del 95 % remuestrea filas (1.000 remuestreos).

## Seguimiento (tracking)

- **Dónde quedó registrado** y **nombre del experimento:** la corrida que fija los parámetros (`reports/06_best_params.json`) se ejecutó **dentro de Databricks** (MLflow del propio workspace, `tracking: databricks`), experimento `proyecto-optimizacion-aprueba-o-no`, ejecución madre `5106d436c4fe4612bdaea74bf6b9ef36` con 25 ejecuciones anidadas. La configuración es automática (`configure_mlflow()`): en un computador sin `.env` cae a MLflow local (`mlflow_local.db`, ignorado por Git; las salidas guardadas en el notebook vienen de una corrida local previa, ejecución madre `1970b3395c3c446b8ca7051eb1786c0f`). Para ver la local: `mlflow ui --backend-store-uri sqlite:///mlflow_local.db`. **No usar `force_local=True` dentro de Databricks:** la carpeta del repo en el workspace es de solo lectura para SQLite (`attempt to write a readonly database`).
- **¿Está cada ensayo como una ejecución con parámetros, métrica y etiquetas?** ☑ sí: el notebook comprueba que hay 25 ejecuciones registradas de 25 ensayos, anidadas en una ejecución madre, con todas las métricas (negocio y técnicas) y etiquetas (`etapa`, `modelo`, `metrica_optimizada`).
- **Mejor ejecución** (identificador y métrica): el ensayo 19, costo 0,2582 en la búsqueda. El identificador de la ejecución madre en Databricks queda en `reports/06_best_params.json`; el de cada ensayo cambia en cada ejecución del notebook y se consulta en la pestaña *Experiments* o con `mlflow.search_runs`.

## Resultados de la búsqueda

- **Mejor costo en la búsqueda: 0,2582** (validación cruzada con 60.000 estudiantes; es optimista). Parámetros: `C = 0,0376` y umbral 0,1666.
- **El umbral que encontró la búsqueda es el teórico:** los 5 mejores ensayos caen entre 0,152 y 0,181 (centro en 0,167 = 1 / 6). Las probabilidades de la regresión logística están razonablemente calibradas para los costos 5 : 1; la calibración formal se evalúa en la etapa 7.
- **`C` casi no importa:** los 5 mejores ensayos tienen `C` entre 0,016 y 0,44 y costos entre 0,2582 y 0,2592, menos que el ruido entre pliegues (≈ 0,002). La importancia estimada por Optuna es 0,95 para el umbral y 0,05 para `C`, pero solo indica que el costo se movía cuando el umbral se alejaba de 0,167.

## Comprobación honesta (estudiantes reservados)

> Modelo con parámetros de **partida** frente al de parámetros **optimizados**, evaluados en los 20.000 estudiantes que la búsqueda no vio. Intervalo del 95 % remuestreando **estudiantes**.

| Modelo | Costo con parámetros de partida (`C = 1`, umbral 0,167) | Costo con parámetros optimizados (`C = 0,0376`, umbral 0,1666) | Diferencia (optimizado − partida) | Intervalo 95 % |
|---|---|---|---|---|
| Regresión logística | 0,2547 | 0,2548 | +0,0001 | [−0,00135; +0,00135] |

Otras métricas en los reservados (partida / optimizado): *log loss* 0,3737 / 0,3736; ROC-AUC 0,8917 / 0,8918; *recall* de `Fail` 0,989 / 0,989; NPV 0,922 / 0,924; alertas por 100: 90,0 / 90,3. «Avisar a todos» cuesta 0,3079 en estos mismos estudiantes.

**Regla de decisión escrita antes de mirar:** usar los parámetros optimizados solo si **todo el intervalo del 95 %** de la diferencia de costo queda por debajo de cero; si cruza el cero, la mejora no se distingue del ruido y se mantienen los de partida.

**Resultado de la regla** (¿todo el intervalo por debajo de cero?): **no**; el intervalo cruza el cero. La mejora no se distingue del ruido.

## Decisión

- **Parámetros que se usarán a partir de ahora** (de partida u optimizados) **y por qué:** los de **partida** (`C = 1`, umbral 1 / 6 ≈ 0,167): son los del torneo, más simples de explicar y la optimización no encontró nada mejor. La regresión logística ya estaba bien configurada.
- **Lo que no pudimos concluir:**
  - Si otros modelos (LightGBM, XGBoost) mejorarían con optimización: no se optimizaron porque el torneo eligió un solo ganador; empataban con la logística sin optimizar.
  - El umbral depende de los **costos 5 : 1**, que son un supuesto. Con otros costos o con una capacidad de tutoría limitada, el umbral cambia (umbral = costo del falso positivo / (costo del falso positivo + costo del falso negativo)).
  - Con ese umbral el modelo avisa a ≈ 90 de cada 100 estudiantes (especificidad ≈ 0,30): la capacidad de tutoría de la institución sigue sin definirse.

> **Una optimización sin mejora no es un fracaso:** documenta que se buscó con un presupuesto y un espacio justificados y que no se encontró nada mejor que la partida.

## Para la clase siguiente

- **Modelo final que pasa a la validación** (prueba abierta una sola vez) y a su registro: **regresión logística**, `C = 1`, umbral 0,167, con las 28 variables de la etapa 4 (`feature_columns(drop=STAGE4_DROP)`, sin indicador de vacío).
- En la etapa 7: abrir `test.joblib` una sola vez, evaluar **calibración** (el umbral teórico sugiere que ya está razonablemente calibrado), **equidad por grupo** (`gender`, `family_income`, `urban_rural`, `school_type`) e interpretación (coeficientes).
