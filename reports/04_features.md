# Informe de variables

> Plantilla en blanco. Resultado de `notebooks/04_features.ipynb`. Cada idea de variable es una
> **hipótesis medida** con la misma validación; se conserva solo si la mejora supera el ruido entre
> pliegues. Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 1.

## Cómo se midió

<!-- Modelo con parámetros fijos, métrica principal y de control, número y tipo de pliegues
     (por qué entidad se parte), semilla. Los MISMOS pliegues para todas las variantes. -->

> Contexto fijo del caso (`data/README.md`): objetivo `pass_70` (aprueba con 70 o más), clase de interés `Fail` (69,2 %); **no se pueden usar** `exam_score`, `pass_status` (corte en 50), `performance_grade`, `performance_level`, `questions_correct` ni `questions_attempted`.

- **Modelo (parámetros fijos):**
- **Métrica principal** (y por qué): costo esperado por estudiante, con *recall* de `Fail` y NPV (propuesta; ver `especificacion-proyecto.md`, sección 4). La referencia a vencer es «avisar a todos» (costo 0,31 con 5 a 1).
- **Métricas de control:** precisión de `Fail` (> 69,2 %), F1 y F2 de `Fail`, PR-AUC de `Fail`, alertas por 100.
- **Pliegues** (cuántos y partidos por qué entidad): por fila, estratificados por `pass_70` (`student_id` es único, no hay entidades repetidas). Cuántos: por definir.
- **Regla de decisión escrita antes de medir:**

## Tabla de ideas medidas

> La fila 0 es la **referencia** (las variables actuales). "Mejora / ruido" = mejora de la métrica
> principal dividida por su desviación entre pliegues; menor que ~1 está dentro del ruido.

| # | Idea (variable y cómo se calcula) | ¿Se conoce al predecir? | Métrica (± ruido) | Mejora / ruido | Decisión |
|---|---|---|---|---|---|
| 0 | **Referencia** | — | | 0 | — |
| 1 | `self_study_share` = `self_study_hours` / `study_hours_per_day` *(idea por medir; no se suman las horas: `self_study_hours` es una parte de `study_hours_per_day` en el 100 % de las filas)* | ☑ sí | | | ☐ conservar ☐ descartar |
| 2 | Indicador de vacío (0/1) de `attendance_percentage`, `previous_gpa` y `time_management_score` *(idea por medir)* | ☑ sí | | | ☐ conservar ☐ descartar |
| 3 | Incluir `time_management_score`, `exam_anxiety_level` y `exam_difficulty` (con y sin) *(idea por medir)* | ☐ sí ☐ no: confirmar cuándo se miden | | | ☐ conservar ☐ descartar |

## Decisiones y motivos

<!-- Una línea por idea: qué decidiste, con qué cifra y por qué. Las ideas descartadas se anotan
     igual: documentan lo que ya probaste. -->

-
-
-

## Supuestos y riesgos

<!-- Variables que solo valen si cierto dato se conoce al momento de decidir; riesgos de fuga;
     lo que complicaría la app si se conserva. -->

-

## Qué se lleva el pipeline final

<!-- La lista final de variables, y dónde está el código (`src/<paquete>/features/`). -->
