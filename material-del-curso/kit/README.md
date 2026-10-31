# Kit del estudiante

Lo que cada grupo recibe en su proyecto: instrucciones para Claude, especificación, prompts, checklist y la plantilla del repositorio.

**Cómo llega al grupo:** no se copia a mano. La raíz de la rama `feature/estudiantes` del curso es la plantilla (`plantilla-repo/`), y `LEEME-PRIMERO.md` explica el flujo: una persona crea un repo público **vacío**, clona la rama `feature/estudiantes` con `--single-branch`, la apunta a ese repo (`git remote set-url origin …`) y hace `push`; los demás clonan el repo del grupo. `material-del-curso/` es de consulta y se borra antes de H3.

Detalle del montaje: `material-del-curso/guias/montaje-proyecto.md`.

---

<!-- contexto-dataset -->
## Aplicación a este proyecto (dataset de rendimiento estudiantil)

Este proyecto trabaja con `data/student_exam_performance.csv` (100.000 estudiantes × 44 columnas). Regla: **se aprueba con 70 o más**. Objetivo: `pass_70`, derivado de `exam_score` (`Fail` 69,2 % = clase de interés). Diccionario de variables: [`data/README.md`](../../data/README.md); decisiones del caso: [`especificacion-proyecto.md`](../../especificacion-proyecto.md).

| Etapa del kit | Dónde está lo de este proyecto |
|---|---|
| Caso de negocio | `reports/00_caso.md`, `especificacion-proyecto.md` |
| EDA y preprocesamiento | `especificaciones/02-eda.md`, `especificaciones/03-preprocesamiento.md`, `reports/01_eda.md` |
| Variables, torneo, optimización | `reports/04_features.md`, `reports/05_torneo.md`, `reports/06_optimizacion.md` |
| Validación, registro, app | `reports/07_validacion.md`, `reports/08_registro.md`, `models/ficha_modelo.md`, `reports/09_despliegue.md` |
