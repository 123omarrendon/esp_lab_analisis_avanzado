# Resumen del trabajo: ¿aprueba o pierde el curso el estudiante?

> Resumen de lo construido sobre `data/student_exam_performance.csv` (100.000 estudiantes × 44 columnas) en las etapas 1 a 5.
> Todas las cifras salen de los notebooks `01b` a `05b` ejecutados con los datos reales, usando **solo el conjunto de entrenamiento** (la prueba sigue cerrada hasta la etapa 7).
> **Estado:** los resultados y las decisiones son **propuestas**; el grupo debe aprobarlas y la institución debe confirmar los supuestos marcados en la sección 7.

## 1. El problema en una frase

Predecir, **antes del examen**, qué estudiantes van a **perder el curso** para ofrecerles apoyo a tiempo.

- **Regla de aprobación:** se aprueba con **70 o más**; con menos de 70 se pierde el curso (69 y 69,99 pierden; 70 aprueba).
- **Objetivo:** `pass_70` (`Pass` / `Fail`), derivado de `exam_score`. **Clase de interés: `Fail`** (69,2 % de los estudiantes = 69.210; `Pass` = 30,8 % = 30.790).
- **No se usa `pass_status`:** el dataset la calcula con corte en 50 (`Fail` 22,6 %), distinto a la regla de la institución. 46.599 estudiantes aprueban con 50 pero pierden con 70.
- **Costo de equivocarse (supuesto, no sale de los datos):** no avisar a quien pierde el curso (falso negativo) cuesta **5**; avisar a quien habría aprobado (falso positivo) cuesta **1**.

## 2. Qué se creó

### Notebooks (en `notebooks/`, ejecutados y con sus salidas guardadas)

| Notebook | Etapa | Basado en | Qué hace |
|---|---|---|---|
| `01b_caso_negocio_aprueba_o_no.ipynb` | 1 · Caso de negocio | `01_caso_negocio.ipynb` | Define la regla de 70, la matriz de costos, las métricas (con ejemplos reales) y las estrategias sin modelo a vencer |
| `02b_eda_aprueba_o_no.ipynb` | 2 · EDA | `02_eda.ipynb` | Explora los datos y termina en una tabla de 9 decisiones, cada una con su motivo |
| `03b_preprocesamiento_aprueba_o_no.ipynb` | 3 · Preprocesamiento | `03_preprocesamiento.ipynb` | Orquesta la limpieza, la partición 80/20 y el guardado de datos |
| `04b_features_aprueba_o_no.ipynb` | 4 · Variables | `04_features.ipynb` y CreditSight | Mide 8 ideas de variables con los mismos pliegues |
| `05b_torneo_aprueba_o_no.ipynb` | 5 · Torneo | `05_torneo.ipynb` y CreditSight | Compara 4 modelos y una línea base; propone 2 finalistas |

Cada uno continúa al anterior y solo **orquesta**: la lógica vive en `src/`.

### Código (`src/proyecto/`) y pruebas (`tests/`)

| Archivo | Para qué sirve |
|---|---|
| `data/cleaning.py` | Carga y limpia: crea `pass_70` (`add_target`), quita las 6 columnas de fuga, marca valores imposibles, separa columnas sensibles para auditoría |
| `data/split.py` | `split_train_test` (80/20 estratificado, semilla 42) y `make_folds` (5 pliegues por fila, estratificados) |
| `features/engineering.py` | Lista de variables, variables nuevas (`add_features`), imputación dentro del `Pipeline` (`build_preprocessor`) |
| `models/train.py` | Candidatos del torneo (`candidates`), `build_pipeline`, métricas de negocio (`business_metrics`), `evaluate_folds`, avisar solo al k % más riesgoso (`top_k_alert`) |
| `tests/test_cleaning.py`, `test_split.py`, `test_features.py`, `test_train.py` (+ `toy.py`) | **66 pruebas** con casos armados a mano; todas pasan |

**Pruebas que pueden fallar:** se introdujeron errores a propósito (por ejemplo `>` en vez de `>=` en el corte de 70, umbral invertido, una columna de fuga entre las variables, partir sin estratificar) y las pruebas los detectaron todos. Dos mutaciones sobrevivieron al principio y se corrigieron las pruebas.

### Documentos `.md` actualizados a la regla de 70

`CLAUDE.md`, `README.md`, `especificacion-proyecto.md`, `data/README.md`, `especificaciones/`, `reports/` (`00_caso`, `01_eda`, `04_features`, `05_torneo`, `06` a `08`, `informe_tecnico`), `models/ficha_modelo.md`, `presentacion/ejecutiva.md` y los bloques «Aplicación a este proyecto» de `material-del-curso/` (el texto original del profesor no se tocó).

## 3. Resultados relevantes por etapa

### Etapa 1 · Caso de negocio (`01b`)
Estrategias **sin modelo** con costos 5 : 1 (costo por estudiante, menor es mejor):

| Estrategia | Costo |
|---|---|
| Nunca avisar | 3,46 |
| Azar según proporciones | 1,28 |
| **Avisar a todos** (la mejor sin modelo) | **0,31** |

- Un modelo supera a «avisar a todos» **solo si su NPV es mayor que 83,3 %** (de los estudiantes que deja tranquilos, más de 5 de cada 6 deben aprobar). Se avisa cuando P(`Fail`) ≥ 1 / (1 + 5) = **0,167**.
- **Por qué la exactitud y el *recall* solos engañan:** como `Fail` es la mayoría (69,2 %), avisar a todos da *recall* 100 % y exactitud 69,2 %. Por eso se usan **costo por estudiante, *recall* de `Fail` y NPV**, con precisión, F1/F2, especificidad y alertas por 100 como apoyo.
- Un 21,8 % de los estudiantes está a menos de 5 puntos del corte de 70.

### Etapa 2 · EDA (`02b`)
- **6 columnas con fuga** (se quitan; el objetivo se crea antes de quitar `exam_score`): `exam_score`, `pass_status`, `performance_grade`, `performance_level`, `questions_correct`, `questions_attempted`.
- **Vacíos** en 7 columnas (3,0 % a 9,9 %); afectan al 41,9 % de las filas, así que **no se borran filas**. Estar vacío no se asocia con perder el curso (`Fail` 68,3–69,4 % frente a 69,2 %).
- `student_id` es único → se parte **por fila**, estratificada.
- **Señal más fuerte** (`Fail` del grupo con valores más bajos → más altos): `previous_exam_score` 90,7 % → 41,7 %; `previous_gpa` 89,6 % → 43,1 %; `study_hours_per_day` 84,1 % → 47,1 %; `exam_difficulty` 51,1 % (fácil) / 70,2 % (media) / 85,1 % (difícil).
- **7 variables sin señal** (AUC ≈ 0,50): `age`, `internet_access`, `private_tuition`, `daily_screen_time`, `physical_activity_hours`, `online_learning_hours`, `online_course_hours`.
- `self_study_hours` es siempre una parte de `study_hours_per_day`: **no se suman** (se contarían dos veces).
- **Equidad:** `family_income` tiene una brecha de **15 puntos** (`Fail` 75,5 % con ingreso bajo, 60,5 % con alto). Por eso `gender` y `family_income` **no entran como predictores** y se guardan aparte para auditar el desempeño por grupo.
- El dataset parece **sintético** (hipótesis).

### Etapa 3 · Preprocesamiento (`03b`)
- 100.000 filas se conservan (no se borra ninguna). Quedan **80.000 de entrenamiento** y **20.000 de prueba**, ambos con 69,2 % de `Fail`.
- Se guardan `train`, `test` y las tablas de auditoría en `data/processed/` (no se versiona). El CSV original **no cambió** (se comprueba con su huella digital).
- La imputación se deja **dentro del `Pipeline`** de la etapa 4 (mediana + indicador de vacío en numéricas; categoría «Desconocido» en las categóricas).

### Etapa 4 · Variables (`04b`) — LightGBM fijo, 5 pliegues por fila

| Idea | Costo | Mejora / ruido | Decisión (propuesta) |
|---|---|---|---|
| Referencia (35 variables) | 0,2579 | — | — |
| **Nueva:** `self_study_share` (= `self_study_hours` / `study_hours_per_day`) | 0,2581 | −0,07 | Descartar |
| **Nueva:** `prep_total_hours` (= horas por día × días de preparación) | 0,2591 | −0,29 | Descartar |
| Sin indicador de vacío | 0,2581 | −0,04 | Quitar |
| Sin `exam_difficulty` | 0,2828 | −14,6 | **Conservar la variable** (con condición) |
| Sin `time_management_score` ni `exam_anxiety_level` | 0,2570 | +0,36 | No concluyente; se conservan por ahora |
| Sin las 7 columnas sin señal | 0,2577 | +0,04 | Quitar |
| **Propuesta final** (sin indicador y sin las 7) | **0,2584** | −0,18 | **28 variables** |

- **Las dos variables nuevas no sirven.** `self_study_share` tiene la misma mediana en quien aprueba y en quien pierde (0,698 y 0,700). `prep_total_hours` se ve distinta a simple vista (29 h frente a 53 h) pero **no baja el costo**: ver diferencia no es mejorar el modelo.
- **`exam_difficulty` es lo que más pesa:** sin ella el costo sube de 0,258 a 0,283 y **el modelo pierde la mitad de su ventaja** sobre «avisar a todos».
- Quitar 7 columnas (incluida `age`, que incluye menores) y el indicador de vacío **no cuesta nada**: un modelo con 28 variables es más simple.

### Etapa 5 · Torneo (`05b`) — 28 variables, mismos 5 pliegues

| Modelo | Costo por estudiante | Precisión de `Fail` | ROC-AUC | Especificidad |
|---|---|---|---|---|
| **Regresión logística** | **0,2576** | **0,760** | 0,892 | 0,299 |
| XGBoost | 0,2583 | 0,759 | 0,894 | 0,296 |
| LightGBM | 0,2584 | 0,759 | 0,894 | 0,295 |
| Random forest | 0,2827 | 0,712 | 0,885 | 0,093 |
| Línea base (avisar a todos) | 0,3079 | 0,692 | 0,500 | 0,000 |

## 4. ¿Qué modelo tiene mejor precisión?

- **Precisión de `Fail`** (de los estudiantes a quienes se avisa, cuántos de verdad pierden el curso): la **regresión logística** es la más alta, 0,760 frente a 0,759 de LightGBM y XGBoost y 0,712 de random forest. La diferencia entre los tres primeros es de 0,001: **es un empate**, no una victoria.
- **Mejor costo:** regresión logística (0,2576), también empatada con XGBoost (0,2583) y LightGBM (0,2584): la diferencia es de 0,1 a 0,2 veces el ruido entre pliegues y ninguno gana en todos los pliegues.
- **Mejor ordenamiento** (ROC-AUC 0,894, PR-AUC 0,950, *log loss* 0,370): LightGBM y XGBoost, por una diferencia de 0,002 sobre la logística.
- **Random forest es el peor** y **pierde en los 5 pliegues** (7,4 a 8,5 veces el ruido). Parte de su desventaja viene de que sus probabilidades están peor calibradas para el umbral de 0,167.
- **Precisión si solo se avisa al 30 % más riesgoso:** 98,3 % la regresión logística y 98,2 % LightGBM y XGBoost (el azar, 68,9 %). Los modelos **ordenan casi perfecto a los más riesgosos**.

**Finalistas propuestos: regresión logística y LightGBM.** La logística gana por simplicidad e interpretabilidad (cada variable tiene un peso explicable) y es la más rápida (0,6 s); LightGBM tiene el mejor ordenamiento y será el rival que ella tiene que batir tras optimizar. Si no supera a la logística, se queda la logística. **El torneo elige finalistas, no un campeón.**

> Una observación: que la regresión logística iguale a los modelos de boosting sugiere que las relaciones con `Fail` son casi lineales (hipótesis; el dataset parece sintético).

## 5. Datos relevantes de los notebooks

- **El modelo supera a «avisar a todos»:** costo 0,258 frente a 0,308 (**ahorro de ≈ 16 %**) con NPV de 91,7 % (mínimo exigido: 83,3 %).
- **Ahorro ilustrativo** por 100.000 estudiantes (el tamaño del dataset; no es un dato de la institución): ≈ 5.000 unidades de costo frente a avisar a todos.
- **Con la regla de la «clase más probable»** (umbral 0,5), la regresión logística cuesta **0,437, peor que no hacer nada** (0,308): la regla de decisión de negocio es indispensable.
- **Peor caso, sin `exam_difficulty`, `time_management_score` y `exam_anxiety_level`:** todos empeoran (logística 0,2576 → 0,2816; LightGBM 0,2584 → 0,2815) y la ventaja sobre la línea base **se reduce a la mitad** (≈ 0,050 → ≈ 0,026). Los tres primeros siguen empatados, por lo que **la elección de finalistas no depende de ese supuesto; el valor del modelo sí.**

## 6. Alertas importantes

1. **El aviso casi no discrimina con el costo 5 : 1:** el modelo avisa a **≈ 90 de cada 100 estudiantes** y deja tranquilo solo al **30 %** de quienes aprobarían (especificidad 0,30). La exactitud (0,78) lo esconde; la exactitud balanceada (0,64) dice la verdad.
2. **Con capacidad limitada, el costo 5 : 1 deja de ser la métrica adecuada.** Si solo se puede avisar al 30 % más riesgoso, el modelo acierta el 98 % de sus alertas, pero el costo sube a 1,99 (frente a 0,308), porque cada estudiante en riesgo sin aviso cuesta 5. La institución debe definir su capacidad real de tutoría.
3. **El umbral de 0,167** supone probabilidades bien calibradas; se ajusta con validación en la etapa 6 y la calibración se evalúa en la etapa 7, **sin usar la prueba**.
4. **Atributos sensibles:** `gender` y `family_income` quedan fuera del modelo; `age` sale por no aportar. La auditoría por grupo (equidad) es de la etapa 7.

## 7. Supuestos pendientes (a confirmar)

| Supuesto | Quién lo confirma |
|---|---|
| Costos 5 : 1 (falso negativo : falso positivo) | La institución |
| `exam_difficulty` (y `time_management_score`, `exam_anxiety_level`) se conoce **antes** de avisar al estudiante; si no, es fuga | La institución |
| Capacidad real de tutoría (alertas por 100) y número de estudiantes por periodo | La institución |
| Quitar `gender` y `family_income` de las variables | El grupo |
| Quitar las 7 columnas sin señal y el indicador de vacío | El grupo |
| Licencia del dataset | Pendiente |

## 8. Qué sigue

1. Confirmar los supuestos de la sección 7.
2. **Etapa 6 · Optimización** de los 2 finalistas (con seguimiento en MLflow) y ajuste del umbral con validación.
3. **Etapa 7 · Validación**: abrir la prueba **una sola vez**, evaluar calibración, equidad por grupo e interpretación.
4. Etapas 8 y 9: registro del modelo y app en Streamlit (la app no consulta Databricks).

## 9. Cómo reproducirlo

```bash
uv pip install -r requirements.txt     # Python 3.12
pytest -q                              # pruebas de data, features y models
# Ejecutar los notebooks en orden: 01b, 02b, 03b, 04b, 05b
# (04b y 05b leen data/processed/train.joblib, que genera 03b)
```

Tablas de resultados: `reports/04_features_tabla.csv` y `reports/05_torneo_tabla.csv`, `05_torneo_tecnicas.csv`, `05_torneo_capacidad.csv`, `05_torneo_peor_caso.csv`. Informes: `reports/01_eda.md`, `reports/04_features.md`, `reports/05_torneo.md`.
