# Informe técnico — TODO: nombre de tu startup

> Esqueleto. Aquí **ensamblas** las secciones que ya escribiste en `reports/`; no las reescribas desde cero: tómalas, ordénalas
> y cuenta una historia coherente. **Se entrega el domingo 15 de noviembre** (hito H4).

> **Regla del informe:** **cada decisión va con su motivo.** Un resultado sin la razón de la decisión que lo produjo es solo un número.

**Grupo:** TODO (integrantes y roles) · **Repositorio:** TODO · **App:** TODO (enlace público)

## Resumen ejecutivo

TODO: 5 a 8 líneas para alguien que no leerá el resto. La decisión de negocio, el resultado en unidades de negocio, el
principal límite y el enlace a la app. *(La conclusión primero.)*

## 1. Caso de negocio

> Fuente: `reports/00_caso.md` (ficha de caso aprobada).

El/la coordinador(a) académico(a) decide qué estudiantes reciben tutoría o refuerzo antes del examen final. Se usan los hábitos de estudio, la asistencia, el historial académico y el contexto de cada estudiante (dataset de Kaggle, 100.000 estudiantes, 44 columnas). Se aprueba con **70 o más**; con menos de 70 el estudiante pierde el curso. El modelo clasifica `pass_70` y busca detectar a quienes perderán el curso (`Fail`, 69,2 %). Equivocarse no cuesta lo mismo: no avisar a quien pierde el curso (falso negativo) es peor que ofrecer una tutoría innecesaria (falso positivo; supuesto 5 a 1). El éxito se mide con el costo por estudiante, el *recall* de `Fail` y el NPV frente a la estrategia sin modelo a vencer, «avisar a todos» (costo 0,31): un modelo la supera solo con NPV > 83,3 %. TODO: costos exactos y capacidad de tutoría acordados con la institución.

## 2. Datos y limpieza

> Fuente: `reports/01_eda.md` y `src/<paquete>/data/`.

- **Unidad de análisis y partición** (y por qué respeta la entidad que se repite): una fila es un estudiante y `student_id` es único (100.000 ids), por lo que se parte por fila, estratificado por `pass_70`, 80/20 y semilla 42.
- **Hallazgos y decisiones** (cada una con su motivo): ver `reports/01_eda.md`. Las principales: se crea `pass_70` desde `exam_score` y se quitan `exam_score`, `pass_status` (corte en 50), `performance_grade`, `performance_level`, `questions_correct` y `questions_attempted` por fuga; no se borran filas con vacíos (7 columnas, 3,0 %–9,9 %), se resuelven dentro del `Pipeline`. TODO: completar cuando el grupo apruebe las decisiones.
- **Datos personales o sensibles y cómo se trataron:** sin nombres ni documentos. `student_id` se excluye; `gender` y `family_income` (brecha de 15 puntos en `Fail`) no entran como predictores y se usan para auditar equidad; `age` (14–20, incluye menores), `family_income`, `parent_education`, `urban_rural` y `school_type` se tratan como sensibles. TODO: decisión final del grupo.

## 3. Variables

> Fuente: `reports/04_features.md`.

Se probaron 8 variantes con LightGBM fijo y 5 pliegues por fila (`notebooks/04b_features_aprueba_o_no.ipynb`). Referencia: 35 variables, costo 0,258 por estudiante frente a 0,308 de «avisar a todos». **Descartadas** (dentro del ruido): `self_study_share`, `prep_total_hours` e indicador de vacío. **Quitadas sin costo:** 7 columnas sin señal (incluida `age`). **Conservada con condición:** `exam_difficulty` (sin ella el costo sube a 0,283: se pierde la mitad de la ventaja sobre «avisar a todos»); es un supuesto de negocio que la institución debe confirmar (¿se conoce al avisar?). Propuesta: 28 variables. Detalle en `reports/04_features.md`. TODO: aprobación del grupo.

## 4. Torneo de modelos

> Fuente: `reports/05_torneo.md`.

Se compararon 4 modelos y una línea base («avisar a todos», costo 0,308) con los mismos 5 pliegues por fila y las 28 variables de la etapa 4 (`notebooks/05b_torneo_aprueba_o_no.ipynb`). **Regresión logística (0,2576), XGBoost (0,2583) y LightGBM (0,2584) empatan** (diferencia de 0,1 a 0,2 veces el ruido); random forest es peor (0,2827; pierde en los 5 pliegues). **Finalistas propuestos: regresión logística y LightGBM.** Advertencias: con el costo 5 : 1 el aviso llega a ≈ 90 de cada 100 estudiantes (especificidad 0,30); sin `exam_difficulty` la ventaja sobre la línea base se reduce a la mitad; el umbral y la calibración se ajustan en las etapas 6 y 7. Detalle en `reports/05_torneo.md`. TODO: aprobación del grupo.

## 5. Optimización y seguimiento

> Fuente: `reports/06_optimizacion.md`.

TODO: espacio de búsqueda, presupuesto, comprobación con datos reservados (¿la mejora fue real o está dentro del ruido?) y qué se
registró en el seguimiento (Databricks o MLflow local).

## 6. Validación e interpretación

> Fuente: `reports/07_validacion.md`.

TODO: decisiones congeladas **antes** de abrir la prueba, resultado en la prueba con su intervalo, comparación con el punto de
partida, errores por segmento o carga de trabajo, interpretación y su límite.

## 7. Registro del modelo

> Fuente: `reports/08_registro.md` y `models/ficha_modelo.md`.

TODO: versión y alias, ida y vuelta, exportación a `models/model.joblib` y esquema de entrada.

## 8. Despliegue

> Fuente: `reports/09_despliegue.md`.

TODO: enlace público, decisiones de despliegue y su motivo, pruebas del enlace, plan B y, si hubo, errores encontrados.

## 9. Riesgos, límites y siguientes pasos

TODO: qué **no** hace el modelo, límites de los datos, uso responsable (variables sensibles o reguladas) y una mejora concreta.

## Anexo: cómo reproducir el proyecto

TODO: pasos mínimos desde un repositorio recién clonado (entorno, datos, orden de los notebooks, `pytest`, `streamlit run`).

---

### Lista de comprobación antes de entregar

- [ ] Las **9 secciones** tienen contenido y **cada decisión lleva su motivo**.
- [ ] Las cifras **coinciden** con `reports/07_validacion.md` y con la presentación.
- [ ] No hay credenciales, `.env` ni datos personales.
- [ ] El enlace de la app abre en una ventana privada.
- [ ] Un tercero puede reproducir el proyecto con el anexo.
