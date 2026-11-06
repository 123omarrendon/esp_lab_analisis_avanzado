# Validación e interpretación

> Resultado de `notebooks/07b_validacion_aprueba_o_no.ipynb` (plantilla del curso: `07_validacion_interpretacion.ipynb`; ejemplo: `material-del-curso/ejemplo-creditsight/notebooks/07_validacion_interpretacion.ipynb`). Código: `src/proyecto/models/validation.py` (12 pruebas en `tests/test_validation.py`).
> **Estado:** medido con la prueba real, abierta **una sola vez**. Las decisiones y su lectura son una **propuesta** hasta que el grupo las apruebe. Datos: `reports/07_metricas_test.json`, `07_decisiones_congeladas.json`, `07_errores_por_segmento.csv`, `07_coeficientes.csv`, `07_importancia_shap.csv`.

## 1. Decisiones congeladas (escritas ANTES de abrir la prueba)

| Decisión | Valor | Cómo se decidió (con qué datos) |
|---|---|---|
| Modelo final | Regresión logística con las 28 variables de la etapa 4 | Torneo con validación cruzada (`reports/05_torneo.md`): empata en costo con LightGBM y XGBoost y se elige por simplicidad e interpretabilidad |
| Parámetros (optimizados o de partida) | **De partida**: `C = 1` | Etapa 6, con 20.000 estudiantes reservados: la mejora (+0,0001, IC [−0,00135; +0,00135]) no se distingue del ruido (`reports/06_optimizacion.md`) |
| ¿Calibrar las probabilidades? | **No** | Sección 2, con los mismos 20.000 reservados (no la prueba) |
| Métrica principal | Costo esperado por estudiante (falso negativo : falso positivo = 5 : 1, **supuesto**); de control: *recall* de `Fail`, NPV y alertas por 100 | Caso de negocio (`reports/00_caso.md`) |
| Regla de decisión | Avisar si P(`Fail`) ≥ 1/6 ≈ 0,167 (= 1 / (1 + 5)) | Fórmula de los costos; la búsqueda de la etapa 6 encontró el mismo valor (0,1666) |
| **Fecha y hora en que se congelaron** | **2026-11-05 20:12:56** (`reports/07_decisiones_congeladas.json`) | La prueba se abrió a las **20:12:58** (`reports/prueba_abierta.txt`). Un ensayo previo, sin abrir la prueba, había guardado las mismas decisiones a las 20:12:36 |

**Regla de comparación escrita antes de mirar:** el modelo «sirve» solo si todo el intervalo del 95 % de la diferencia de costo (modelo − «avisar a todos») queda por debajo de cero **y** el intervalo del NPV queda por encima de 83,3 %.

## 2. Calibración (con estudiantes reservados, no con la prueba)

- ¿Se evaluó? ☑ sí.
- **Regla escrita de antemano:** calibrar solo si el *log loss* mejora en más de 0,005 y el costo no empeora de forma distinguible.
- **Resultado** (20.000 reservados, sigmoide con validación cruzada dentro del 75 % de búsqueda): *log loss* 0,3737 sin calibrar y 0,3737 calibrado; costo 0,2547 en ambos; diferencia de costo 0,0000 con IC [−0,00085; +0,00060]. **No mejora nada: no se calibra.** La curva de calibración (en el notebook) queda sobre la diagonal: la regresión logística ya da probabilidades bien calibradas, lo que justifica el umbral teórico de 1/6.

## 3. La prueba, abierta **una sola vez**

- Fecha y hora en que se abrió: **2026-11-05 20:12:58** (marca en `reports/prueba_abierta.txt`). 20.000 estudiantes, `Fail` = 69,2 %; ninguno comparte `student_id` con el entrenamiento (el notebook lo comprueba).
- ¿Se cambió algo del modelo después de verla? ☑ **no.** Al re-ejecutar el notebook, `open_test_once` reutiliza las probabilidades guardadas y no vuelve a evaluar la prueba.

| Métrica | Modelo final | «Avisar a todos» (baseline) | Intervalo del 95 % (estudiantes) |
|---|---|---|---|
| **Costo por estudiante** (principal; menor es mejor) | **0,2550** | 0,3079 [0,3016; 0,3142] | [0,2467; 0,2634] |
| *Recall* de `Fail` (control) | 0,988 | 1,000 | [0,986; 0,990] |
| NPV (control; mínimo exigido 0,833) | 0,919 | no existe (no tranquiliza a nadie) | [0,907; 0,930] |
| Alertas por 100 | 89,7 | 100 | [89,3; 90,1] |
| Precisión de `Fail` / especificidad | 0,763 / 0,308 | 0,692 / 0,000 | — |
| ROC-AUC / PR-AUC / *log loss* | 0,896 / 0,950 / 0,368 | — | — |

**¿Mejora al baseline con confianza?** **Sí.** Diferencia de costo (modelo − «avisar a todos») = **−0,0529**, IC [−0,0604; −0,0455], todo por debajo de cero; y el límite inferior del NPV (0,907) supera 0,833. Ahorro de ≈ 17 % del costo (0,053 por estudiante). Es consistente con lo visto en validación cruzada y en los reservados (0,2547): no hubo pérdida de generalización.

## 4. Errores y carga de trabajo

> Tabla completa en `reports/07_errores_por_segmento.csv` (casos, % real de `Fail`, % de alertas, *recall*, precisión, NPV, costo por grupo).

| Segmento | Casos | % `Fail` real | % alertas | *Recall* | NPV |
|---|---|---|---|---|---|
| `family_income` Low | 3.846 | 76,4 | 93,2 | 0,990 | **0,888** |
| `family_income` High | 2.044 | 59,7 | 84,0 | 0,984 | 0,942 |
| `gender` Female / Male | 9.804 / 9.812 | 69,4 / 68,9 | 89,6 / 89,6 | 0,988 / 0,987 | 0,921 / 0,914 |
| `gender` Other | 384 | 70,1 | 92,4 | 1,000 | 1,000 (inestable: pocos tranquilizados) |
| `urban_rural` Rural / Urban | 4.034 / 8.907 | 69,8 / 69,2 | 90,8 / 89,4 | 0,988 / 0,988 | 0,911 / 0,922 |
| `school_type` Charter / Private / Public | 2.037 / 6.983 / 10.980 | 71,9 / 68,5 / 69,2 | 90,1 / 89,7 / 89,6 | 0,991 / 0,989 / 0,987 | 0,936 / 0,923 / 0,913 |
| Edad ≤ 15 / 16–17 / ≥ 18 | 5.654 / 5.638 / 8.708 | 69,3 / 69,2 / 69,2 | 89,7 / 89,4 / 89,8 | 0,987 / 0,986 / 0,989 | 0,916 / 0,908 / 0,928 |

- **¿Hay un segmento al que le va peor?** El *recall* es casi igual en todos los grupos (brecha máxima 0,013, en `gender` por la categoría `Other`, de solo 384 casos). El grupo con menor *recall* es `family_income` Upper-Middle (0,980). **La diferencia que sí se ve es en alertas y NPV por ingreso:** a `Low` se le avisa al 93,2 % y a `High` al 84,0 %, y el NPV baja a 0,888 en `Low` (de los que el modelo deja tranquilos, 11 % igual pierde el curso) frente a 0,942 en `High`. Las alertas siguen la brecha **real** de `Fail` (76,4 % frente a 59,7 %; 16,7 puntos), pese a que `family_income` **no entra al modelo**: otras variables (p. ej. nota previa, asistencia, horas de estudio) la reemplazan. Es una hipótesis, no se probó.
- **Carga de trabajo:** el modelo avisa a **≈ 90 de cada 100** estudiantes, cuando en realidad pierden el curso 69. Si la institución solo pudiera tutorar al 30 % más riesgoso: precisión 0,983 pero *recall* 0,426 y costo 1,99 (frente a 0,308 de avisar a todos). **Con capacidad limitada el costo 5 : 1 deja de ser la métrica adecuada**; la capacidad real sigue sin definirse.

## 5. Interpretación

- **Variables que más pesan** (coeficientes de la regresión logística, variables estandarizadas; `reports/07_coeficientes.csv`): `exam_difficulty` (Difícil: coeficiente +1,50, *odds ratio* 4,5; Fácil: −1,32), nota previa del examen (−1,47: cada desviación estándar más de nota previa multiplica por 0,23 las probabilidades relativas de perder), horas de estudio por día (−0,83), pruebas de práctica completadas (−0,64), días de preparación (−0,50), asistencia (−0,42), horas de sueño (−0,39) y estrés (+0,33). Por SHAP el orden es: nota previa (1,19), horas de estudio (0,64), `exam_difficulty` (≈ 0,5 cada categoría), pruebas de práctica (0,50). Para el negocio: pierde el curso quien llega con baja nota previa, estudia y practica poco, y enfrenta un examen difícil; son variables **accionables** (estudio, práctica, asistencia) salvo la dificultad y la nota previa.
- **Límite de la explicación:** explica **al modelo, no al mundo**; no dice si el modelo acertó ni que esas variables *causen* el resultado. Las variables correlacionadas (p. ej. horas de estudio y días de preparación) se reparten el crédito, y las dos medidas (coeficientes y SHAP) ordenan distinto porque miden cosas distintas. El dataset parece sintético (hipótesis): las relaciones casi lineales pueden no repetirse con datos reales.
- **Atributos sensibles o de uso regulado entre las variables:** el modelo **usa** `parent_education`, `urban_rural` y `school_type`; **no usa** `age`, `gender` ni `family_income` (solo se auditan). Las tres que usa reparten solo el **4,2 %** de la influencia total (la mayor: `school_type_Public`, |SHAP| 0,05, frente a 1,19 de la nota previa). Auditoría por `gender`, `family_income`, `urban_rural` y `school_type`: tabla del apartado 4. El dataset incluye menores de edad (≤ 17: 56 % de la prueba): el desempeño es parejo por tramos de edad.
- **Riesgo que se mantiene:** `exam_difficulty` es la variable más pesada y solo es válida si **se conoce antes de avisar**. Si no, es fuga y el resultado de la prueba sería optimista (ver peor caso en `reports/05_torneo.md`: la ventaja sobre «avisar a todos» se reduce a la mitad).

## 6. Conclusión

- **¿El modelo sirve para la decisión del caso? ¿Con qué condiciones?** Sí, **para decidir a quién avisar** con costos 5 : 1: ahorra ≈ 17 % frente a «avisar a todos» con confianza del 95 %, y se comprobó con estudiantes que nunca se usaron para decidir. Condiciones: (1) la institución confirma los costos 5 : 1; (2) `exam_difficulty` se conoce antes de avisar; (3) la institución define su capacidad de tutoría, porque el modelo avisa a ≈ 90 de cada 100 y deja tranquilo a pocos (especificidad 0,31). El resultado se llama **propuesta** hasta que el grupo lo apruebe.
- **Qué NO debe hacerse con él:**
  - No usarlo para excluir ni sancionar a un estudiante: es un aviso de apoyo, no un juicio.
  - No leer los coeficientes ni SHAP como causas.
  - No usar la regla de la «clase más probable» (umbral 0,5): cuesta más que no hacer nada.
  - No confiar en el NPV de grupos pequeños (p. ej. `gender` = `Other`, 384 casos).
  - No asumir que el desempeño se mantiene con otra población o con otros costos sin volver a validar.
  - Al ser la prueba ya abierta, **no se vuelve a usar para decidir**; cualquier cambio de modelo, umbral o variables debe declararse y validarse con nuevos datos.
- **Lo que no pudimos concluir:** si la brecha en alertas y NPV por ingreso es aceptable para la institución (es decisión de política, no técnica); por qué el modelo alerta más a `Low` si no usa `family_income` (hipótesis sin probar); y el verdadero valor de negocio, que depende de costos y capacidad que no salen de los datos.
