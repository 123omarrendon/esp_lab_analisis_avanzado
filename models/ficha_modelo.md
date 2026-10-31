# Ficha del modelo

> Plantilla en blanco. Complétala a mano con **tus** resultados (los de la prueba de `reports/07_metricas_test.json`).
> Un documento corto que cualquiera pueda leer antes de usar el modelo: qué es, con qué datos, qué rendimiento tiene
> y **qué no hay que hacer con él**.

## Qué es

Estima la probabilidad de que un estudiante pierda el curso (`pass_70` = `Fail`, nota menor que 70; se aprueba con 70 o más), para que el/la coordinador(a) académico(a) priorice la tutoría o el refuerzo antes del examen final. Es una alerta para revisión humana, no una decisión automática.

- **Modelo:** _______________
- **Registro:** _______________ versión _______________, alias `champion` (Databricks o local)
- **Regla de decisión:** _______________  (clase más probable, umbral o menor costo esperado)

## Datos de entrenamiento

- **Fuente y licencia:** Student Exam Performance & Success Dataset (Mobeen Fatimah, Kaggle). Licencia: _______________ (pendiente de verificar)
- **Tamaño:** 100.000 filas de 100.000 entidades (un estudiante por fila)
- **Partición:** por fila, estratificada por `pass_70` (la unidad de análisis es un estudiante y `student_id` es único); la prueba se abrió **una sola vez**: _______________
- **Datos personales:** sin nombres ni documentos; `student_id` y `gender` no entran al modelo. `age` (14–20, incluye menores) y otros atributos demográficos se tratan como sensibles.

## Rendimiento (prueba, entidades nunca vistas)

| Métrica | Valor | Intervalo del 95 % |
|---|---|---|
| Métrica principal | | |
| Baseline | | |
| Control 1 | | |

## Variables que más pesan

_______________

## Límites y usos no recomendados

- Datos con los que se entrenó (¿sintéticos, de una época, de una región?): dataset público de Kaggle sin fecha ni región; hay indicios de origen sintético (varias variables sin relación con la nota, `study_method` repartido en cinco partes iguales). A confirmar.
- Supuestos de negocio de los que depende (p. ej. una variable que debe conocerse al decidir): todas las variables de entrada deben conocerse **antes del examen**. Por eso se excluyen `exam_score`, `pass_status` (corte en 50), `performance_grade`, `performance_level`, `questions_correct` y `questions_attempted`. Con 69,2 % de `Fail`, el modelo solo aporta si supera a «avisar a todos» (NPV > 83,3 % con costos 5 a 1).
- Atributos sensibles o de uso regulado: `gender` (fuera del modelo), `age` (menores de edad), `family_income`, `parent_education`, `urban_rural`, `school_type`.
- Qué **no** debe hacerse con este modelo: sancionar, excluir o limitar oportunidades de un estudiante; usarlo como única base de una decisión; interpretarlo como explicación de causas.
- Lo que **no se evaluó** (estabilidad en el tiempo, otros grupos, deriva): _______________

## Reproducibilidad

Código en `src/`, pruebas en `tests/`, notebooks en `notebooks/`.
