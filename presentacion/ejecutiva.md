---
marp: true
theme: default
paginate: true
header: "Presentación ejecutiva · TODO: nombre de tu startup"
footer: "Casos Avanzados · Maestría en Ingeniería Analítica"
---

# 1 · Problema

<!-- TODO: borra las instrucciones de cada diapositiva y escribe lo tuyo. MÁXIMO 5 DIAPOSITIVAS: no agregues una sexta. -->

- **¿Quién decide?** El/la coordinador(a) académico(a)
- **¿Qué decide con el resultado?** A qué estudiantes ofrecer tutoría o refuerzo antes del examen final
- **¿Cuánto cuesta equivocarse** (y si cuesta distinto en cada dirección)? Sí cuesta distinto: no avisar a quien perderá el curso (nota menor que 70) es peor que ofrecer una tutoría que no hacía falta. TODO: cifra en unidades de negocio

> TODO: un titular que entienda alguien sin formación técnica. **No abras con el nombre del algoritmo.**

---

# 2 · Enfoque

<!-- TODO: una frase por idea. Lo técnico va al informe, no aquí. -->

- **Los datos:** dataset público de Kaggle con 100.000 estudiantes y 44 variables; se aprueba con 70 o más y 69,2 % no llegó a 70
- **Cómo se validó con honestidad:** cada fila es un estudiante distinto, así que se parte por fila, con la misma proporción de reprobados en entrenamiento y prueba; se quitaron las variables que ya contienen la nota del examen
- **Qué se comparó y qué se eligió:** TODO
- **Qué se descartó y por qué:** TODO (si una idea no funcionó, dilo: da credibilidad)

---

# 3 · Resultado y costo de negocio

<!-- TODO: las cifras salen de reports/07_validacion.md. No inventes ni redondees a tu favor. -->

| | Sin el modelo (punto de partida) | Con el modelo |
|---|---|---|
| Resultado en unidades de negocio | TODO | TODO |
| Con TODO decisiones al mes | TODO | TODO |

- **Mejora y su intervalo o límite:** TODO
- **La métrica técnica** (F1, AUC, RMSE…) va en una nota, no en el titular: TODO

---

# 4 · Demo de la app

<!-- TODO: enlace público de tu app (ábrelo antes de exponer: puede estar dormida). -->

**Enlace:** TODO

1. **Un caso normal:** TODO (qué datos escribes y qué responde)
2. **Un caso límite:** TODO (uno que cambia la decisión)
3. **Un dato inválido:** TODO (la app lo rechaza con un mensaje claro)

> Plan B: captura de pantalla con fecha y la app en local.

---

# 5 · Riesgos y siguientes pasos

<!-- TODO: la diapositiva que más credibilidad da si es honesta. «No hay riesgos» no es una respuesta. -->

- **Qué NO hace el modelo** (y qué decisión no debe tomar solo): TODO
- **Límites de los datos:** TODO
- **Uso responsable** (variables sensibles o reguladas): TODO
- **Siguientes pasos:** TODO (una mejora concreta y qué vigilarían en producción)
