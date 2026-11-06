# Registro del modelo

> Resultado de `notebooks/08b_registro_modelo_aprueba_o_no.ipynb` (plantilla del curso: `08_registro_modelo.ipynb`, sin modificar; ejemplo: `material-del-curso/ejemplo-creditsight/notebooks/08_registro_modelo.ipynb`).
> **Estado:** ejecutado el 2026-11-05 20:25. El registro quedó en **MLflow local**, no en Databricks (ver sección 1). Datos: `reports/08_registro.json` y `reports/08_evolucion_modelo.csv`.

## 1. Dónde quedó registrado

| Dato | Valor |
|---|---|
| Plataforma | ☐ Databricks  ☑ MLflow local (respaldo) → motivo: no hay archivo `.env` en este equipo (solo `.env.example`), así que `configure_mlflow()` cayó al respaldo local. Para registrarlo en Databricks hay que completar `.env` (`PROFILE`, o `DATABRICKS_HOST` y `DATABRICKS_TOKEN`) y volver a ejecutar el notebook (el modelo se guardaría en Unity Catalog como `catálogo.esquema.estudiantes_aprueba_o_no`) |
| Experimento | `proyecto-registro-aprueba-o-no` |
| Nombre del modelo registrado | `estudiantes_aprueba_o_no` |
| Versión | 1 |
| Alias | `champion` → versión 1 |
| Ejecución (run id) | `29f92c8497174db78e90cd12220ca183` |
| Quién lo registró y cuándo | Sesión del usuario `omar`, desde el notebook, 2026-11-05 20:25:40. El registro está en `mlflow_local.db` (raíz del repo) |

## 2. Qué se registró junto al modelo

- **Parámetros:** `modelo` = regresión logística, `C` = 1, `umbral` = 0,1667 (1/6), `calibrado` = False, `n_variables` = 28.
- **Métricas de la prueba** (32, con prefijo `test_`; la prueba se abrió una sola vez en la etapa 7): costo 0,2550 con su intervalo del 95 % [0,2467; 0,2634]; costo de «avisar a todos» 0,3079; diferencia −0,0529 [−0,0604; −0,0455]; *recall* de `Fail` 0,988; NPV 0,919; alertas por 100: 89,7; ROC-AUC 0,896; *log loss* 0,368; entre otras.
- **Firma y ejemplo de entrada** (¿qué columnas espera?): las **28 columnas** de la etapa 4 (12 numéricas y 16 categóricas, `feature_columns(drop=STAGE4_DROP)`), todas conocidas antes del examen; nunca `exam_score`, `pass_status`, `performance_grade`, `performance_level`, `questions_correct`, `questions_attempted`, `student_id`, `gender` ni `family_income` (ver `data/README.md`). Salida: probabilidades de `Pass` y `Fail`. Lista completa en `reports/08_registro.json`.
- **Etiquetas:** `etapa` = 08_registro; `decisiones_congeladas` = 2026-11-05T20:12:56; `unidad_de_particion` = fila (`student_id` único); `supera_baseline` = True; `nota` (prueba abierta una sola vez; los costos 5 : 1 son un supuesto).

## 3. Comprobación de ida y vuelta

- ¿El modelo recuperado del registro predice igual que el local? ☑ sí.
- **Cómo se comprobó:** se cargó `models:/estudiantes_aprueba_o_no@champion` y se compararon las probabilidades de `Fail` de 500 estudiantes del entrenamiento con las del objeto registrado: diferencia máxima **0,0**, y las mismas alertas con el umbral 1/6. La prueba no interviene en esta etapa.

## 4. Tracking frente a registro (en tus palabras)

- **Tracking:** en la etapa 6 guardó cada uno de los 25 ensayos de la búsqueda (valores de `C` y umbral, costo y demás métricas) para poder compararlos y reproducirlos; el resultado fue que ninguno mejoraba de forma medible a los parámetros de partida.
- **Registro:** guarda **un solo** modelo, el final, con su versión, firma, ejemplo de entrada y métricas de la prueba. El alias `champion` ayuda porque quien lo use pide «el champion» y no necesita saber el número de versión: si algún día hay una versión mejor se mueve el alias y no se cambia ningún código (la app, en cambio, no consulta el registro y usa el archivo `model.joblib` del notebook 09).

## 5. ¿Mejoró el modelo con las iteraciones? (notebooks 07b y 08)

> Tabla completa en `reports/08_evolucion_modelo.csv`, calculada leyendo los archivos de cada etapa. Los costos de filas con estudiantes distintos **no son comparables entre sí** (±0,003 entre subconjuntos es normal): cada cambio se mide contra lo anterior en los mismos estudiantes.

| Etapa y cambio | Estudiantes | Costo | ¿Mejoró de forma distinguible? |
|---|---|---|---|
| 0 · Sin modelo: «avisar a todos» | validación cruzada (80.000) | 0,3079 | punto de partida |
| 4 · Primer modelo, 35 variables (LightGBM) | validación cruzada | 0,2579 ± 0,0048 | **Sí** (−0,050, unas 10 veces el ruido) |
| 4 · 28 variables (−7 sin señal, sin indicador de vacío) | validación cruzada | 0,2584 ± 0,0030 | No (−0,0005); queda más simple |
| 5 · Torneo: regresión logística | validación cruzada | 0,2576 ± 0,0032 | No (+0,0008, empate); se elige por simplicidad |
| 6 · `C` y umbral optimizados (25 ensayos) | 20.000 reservados | 0,2548 frente a 0,2547 | No (+0,0001, IC [−0,0014; +0,0014]) |
| 7 · Calibración | 20.000 reservados | 0,2547 frente a 0,2547 | No (0,0000, IC [−0,0008; +0,0006]); no se calibró |
| 7 · **Prueba**, modelo sin cambios | 20.000 de la prueba | **0,2550** [0,2467; 0,2634] | **Sí** frente a «avisar a todos» (−0,0529, IC [−0,0604; −0,0455]) |

**Conclusión honesta:**
- El modelo **sí** mejoró frente a no tener modelo (−0,053 por estudiante, ≈ 17 %), y esa es **la única mejora real**: ya estaba en el primer modelo.
- Las iteraciones posteriores (menos variables, otro modelo, optimización, calibración) **no mejoraron el costo de forma medible**. Dejaron un modelo más simple, calibrado y explicable, y probaron que no quedaba nada más por ganar con `C`, el umbral o la calibración.
- La prueba (0,2550) coincide con los reservados (0,2547): elegir con validación no infló el resultado.
- **Registrar el modelo (esta etapa) no lo cambió:** la ida y vuelta da la misma predicción.
- Lo que sí movió el costo fue `exam_difficulty` (sin ella sube de 0,258 a 0,283), que es un supuesto de negocio pendiente.
- Lo que **no** mejoró y sigue igual: el modelo avisa a ≈ 90 de cada 100 estudiantes, y se avisa más a ingreso `Low` (93,2 %) que a `High` (84,0 %).

## 6. Reproducibilidad

- ¿Alguien de otro grupo podría recuperar tu modelo con lo que dejaron escrito? ☐ sí  ☑ **parcialmente** → qué falta:
  - El registro está en `mlflow_local.db`, un archivo binario del repo; `models/final_pipeline.joblib` **no se versiona** (hay que regenerarlo con el notebook 07b).
  - **Versión de MLflow:** `requirements.txt` fija `mlflow==3.17.1`, pero `mlflow_local.db` tiene un esquema de MLflow **3.18.0** y 3.17.1 no lo abre (error *out-of-date database schema*). Hay que fijar `mlflow==3.18.0` en `requirements.txt` o regenerar la base; no se cambió `requirements.txt` aquí.
  - Aún no está en Databricks (falta `.env`).
  - Los supuestos de negocio (costos 5 : 1, `exam_difficulty` conocida antes de avisar) deben confirmarlos la institución y el grupo.
