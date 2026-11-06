# Ficha del modelo

> Documento corto para leer antes de usar el modelo: qué es, con qué datos, qué rendimiento tiene y **qué no hay que hacer con él**.
> Cifras de la prueba de `reports/07_metricas_test.json` (etapa 7, `notebooks/07b_validacion_aprueba_o_no.ipynb`) y registro de `reports/08_registro.json` (etapa 8). **Propuesta** hasta que el grupo la apruebe.

## Qué es

Estima la probabilidad de que un estudiante pierda el curso (`pass_70` = `Fail`, nota menor que 70; se aprueba con 70 o más), para que el/la coordinador(a) académico(a) priorice la tutoría o el refuerzo antes del examen final. Es una alerta para revisión humana, no una decisión automática.

- **Modelo:** regresión logística (`C = 1`) con las 28 variables de la etapa 4, sin calibrar (la calibración no mejoró nada).
- **Registro:** MLflow **local** (`mlflow_local.db`), modelo `estudiantes_aprueba_o_no` versión 1, alias `champion` (registrado el 2026-11-05; todavía no está en Databricks).
- **Regla de decisión:** avisar si P(`Fail`) ≥ 1/6 ≈ 0,167 (menor costo esperado con costos 5 : 1, **supuesto** a validar con la institución).

## Datos de entrenamiento

- **Fuente y licencia:** Student Exam Performance & Success Dataset (Mobeen Fatimah, Kaggle). Licencia: _pendiente de verificar_.
- **Tamaño:** 100.000 filas de 100.000 entidades (un estudiante por fila); 80.000 de entrenamiento y 20.000 de prueba.
- **Partición:** por fila, estratificada por `pass_70` (la unidad de análisis es un estudiante y `student_id` es único); la prueba se abrió **una sola vez**: 2026-11-05 20:12:58 (`reports/prueba_abierta.txt`), con las decisiones congeladas a las 20:12:56.
- **Datos personales:** sin nombres ni documentos; `student_id` y `gender` no entran al modelo. `age` (14–20, incluye menores) y otros atributos demográficos se tratan como sensibles.

## Rendimiento (prueba, estudiantes nunca vistos)

| Métrica | Valor | Intervalo del 95 % |
|---|---|---|
| Costo por estudiante (principal; 5 : 1; menor es mejor) | **0,2550** | [0,2467; 0,2634] |
| Baseline: «avisar a todos» | 0,3079 | [0,3016; 0,3142] |
| Diferencia (modelo − baseline) | −0,0529 (≈ 17 % menos) | [−0,0604; −0,0455] |
| *Recall* de `Fail` | 0,988 | [0,986; 0,990] |
| NPV (mínimo exigido 0,833) | 0,919 | [0,907; 0,930] |
| Alertas por 100 estudiantes | 89,7 | [89,3; 90,1] |

Supera a «avisar a todos» con confianza del 95 %. Con estos costos el modelo avisa a ≈ 90 de cada 100 estudiantes y deja tranquilo a pocos (especificidad 0,31): el ahorro viene de no tranquilizar por error a quien pierde el curso.

## Variables que más pesan

Por coeficientes (variables estandarizadas) y SHAP: `exam_difficulty` (Difícil empuja hacia `Fail`, *odds ratio* 4,5; Fácil hacia `Pass`), nota previa del examen (`previous_exam_score`), horas de estudio por día, pruebas de práctica completadas, días de preparación, asistencia, horas de sueño y estrés. Las variables sensibles que el modelo sí usa (`parent_education`, `urban_rural`, `school_type`) reparten solo el 4,2 % de la influencia. Explica al modelo, no al mundo: no son causas.

## Límites y usos no recomendados

- Datos con los que se entrenó (¿sintéticos, de una época, de una región?): dataset público de Kaggle sin fecha ni región; hay indicios de origen sintético (varias variables sin relación con la nota, `study_method` repartido en cinco partes iguales). A confirmar. Que las relaciones sean casi lineales puede no repetirse con datos reales.
- Supuestos de negocio de los que depende: los costos 5 : 1 (supuesto); y que todas las variables de entrada se conozcan **antes del examen**, en especial `exam_difficulty`: sin ella el costo sube de 0,258 a 0,283 y la ventaja sobre «avisar a todos» se reduce a la mitad. Por eso se excluyen `exam_score`, `pass_status` (corte en 50), `performance_grade`, `performance_level`, `questions_correct` y `questions_attempted`.
- Atributos sensibles o de uso regulado: `gender` (fuera del modelo), `age` (menores de edad; fuera del modelo), `family_income` (fuera del modelo), `parent_education`, `urban_rural`, `school_type` (dentro).
- **Equidad (auditada en la prueba):** el *recall* es casi igual en todos los grupos (brecha ≤ 0,013), pero se avisa al 93,2 % de ingreso `Low` y al 84,0 % de `High`, y el NPV baja a 0,888 en `Low` (frente a 0,942 en `High`). Aunque `family_income` no entra al modelo, las alertas siguen su brecha real de `Fail`. Las cifras de `gender` = `Other` (384 casos) son inestables.
- Qué **no** debe hacerse con este modelo: sancionar, excluir o limitar oportunidades de un estudiante; usarlo como única base de una decisión; interpretarlo como explicación de causas; usar la regla de la «clase más probable» (umbral 0,5), que cuesta más que no hacer nada.
- Lo que **no se evaluó** (estabilidad en el tiempo, otros grupos o instituciones, deriva): no hay datos para hacerlo. La prueba ya se abrió y no se vuelve a usar para decidir.

## Reproducibilidad

Código en `src/`, pruebas en `tests/`, notebooks en `notebooks/` (07b para validar, 08 para registrar). `mlflow_local.db` se generó con MLflow 3.18.0, distinta de la fijada en `requirements.txt` (3.17.1): ver `reports/08_registro.md`.
