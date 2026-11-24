---
inclusion: always
---

# Glosario

Términos del dominio. En el código se usa el **identificador** indicado y ningún sinónimo.

| Término | Identificador | Definición |
|---------|---------------|------------|
| Perfil | `usuario` | Persona que usa Rumbo. En el MVP se identifica con una cookie, sin contraseña. |
| Espacio | `espacio` | Un curso o examen con su fecha. Contiene documentos, temario y una ruta. |
| Documento | `documento` | Archivo subido (PDF, PPTX, DOCX, imagen). Puede marcarse como sílabo. |
| Sílabo | `es_silabo` | Documento opcional que guía la detección y el orden de los temas. |
| Fragmento | `fragmento` | Trozo de texto de un documento, de una sola página o diapositiva, con su embedding. Es la unidad que se cita. |
| Cita | `cita` | Referencia a un fragmento: documento + página o diapositiva. Toda respuesta generada lleva al menos una. |
| Temario | `temario` | Conjunto de temas y subtemas de un espacio. |
| Tema / subtema | `tema` (con `tema_padre_id`) | Unidad de contenido. Los subtemas son temas con padre. La ruta planifica subtemas (o temas sin hijos). |
| Prerrequisito | `tema_prerrequisito` | Relación "A debe estudiarse antes que B". Forma un grafo sin ciclos. |
| Importancia | `importancia` | 1 (complementario), 2 (normal), 3 (esencial). Decide qué entra en el modo rescate. |
| Diagnóstico | `diagnostico` | Prueba inicial opcional de 5 a 10 preguntas para saltar lo que ya se sabe. |
| Ruta | `ruta` | Plan día por día desde hoy hasta el examen. Pertenece a un usuario y a un espacio. |
| Versión de ruta | `ruta.version` | Aumenta cada vez que se replanifica. |
| Sesión planificada | `sesion_planificada` | Bloque de estudio asignado a una fecha dentro de la ruta. Tipos: `estudio`, `repaso`, `simulacro`, `margen`. |
| Sesión | `sesion` | Ejecución real de una sesión planificada (o de una sesión mínima): inicio, pausa, fin, resultados. |
| Sesión mínima | `es_minima` | Sesión de 5 minutos (flashcards vencidas + 2 preguntas) que mantiene la racha. |
| Sesión fijada | `esta_fijada` | Sesión que el usuario movió a mano en el calendario. La replanificación no la mueve. |
| Día de margen | tipo `margen` | Día reservado para imprevistos. La replanificación lo usa primero cuando hay atraso. |
| Simulacro | tipo `simulacro` | Examen de práctica con preguntas mezcladas de toda la ruta, en los últimos días. |
| Mini simulacro | `mini_simulacro` | 10 preguntas mezcladas de la síntesis semanal. |
| Replanificación | `replanificar` | Recalcular las sesiones futuras con lo pendiente, sin acumular tareas vencidas. |
| Modo rescate | `modo_rescate` | Estado de la ruta cuando el tiempo no alcanza: solo se planifican los temas esenciales y sus prerrequisitos. |
| Pregunta | `pregunta` | Ítem de práctica de opción múltiple con explicación y cita. |
| Flashcard | `flashcard` | Tarjeta anverso/reverso con cita. Su estado de repaso es por usuario. |
| Repetición espaciada | `estado_flashcard` | Programación de repasos con el algoritmo SM-2. |
| Dominio | `dominio_tema` | Qué tanto domina el usuario un tema (0 a 1) y su estado: `dominado`, `en_progreso`, `debil`, `no_visto`. |
| Riesgo | `riesgo_diario` | Puntaje 0–100 de probabilidad de abandono, con nivel `bajo`, `medio`, `alto` o `critico`. |
| Ritmo | — | Forma amable de mostrar el riesgo al usuario ("Vas a buen ritmo"). |
| Intervención | `intervencion` | Acción que Rumbo toma según el nivel de riesgo. |
| Resumen diario | `resumen_diario` | Resumen de la mañana sobre lo estudiado ayer. |
| Síntesis semanal | `sintesis_semanal` | Mapa conceptual, mini simulacro, gráfico y plan de refuerzo del domingo. |
| Plan de refuerzo | `plan_refuerzo` | Temas débiles que la ruta prioriza la semana siguiente. |
| XP | `evento_xp` | Puntos de experiencia por práctica. Solo para la gamificación personal. |
| Nivel | `nivel` | Se calcula a partir del XP acumulado en una ruta. |
| Racha | `racha` | Días seguidos con al menos una sesión completada (incluida la mínima). |
| Comodín | `comodin` | Protege la racha un día sin estudio. Uno por semana. |
| Insignia | `insignia` | Logro por hito ("Volví", "7 días seguidos"…). |
| Amigo | `amistad` | Relación aceptada entre dos usuarios. |
| Empujón | `empujon` | Mensaje corto de ánimo de un amigo. |
| Enlace para compartir | `enlace_ruta` | Enlace con código que permite copiar una ruta. |
| Ruta original | `ruta_origen_id` | Ruta de la que se copió otra. Las copias de una misma ruta original forman ligas. |
| Liga | `liga` | Grupo de 10 a 30 personas que siguen la misma ruta original, con ranking semanal. |
| Puntaje de avance | `puntaje_avance` | Porcentaje de la ruta completado durante la semana. |
| Puntaje de constancia | `puntaje_constancia` | Días activos en la semana (0 a 7). |
| Día activo | — | Día con al menos 5 preguntas o flashcards respondidas. Abrir la app no cuenta. |
| Modo anónimo | `es_anonimo` | Aparecer en la liga con un alias en vez del nombre. |
| Modo demo | `MODO_DEMO` | Configuración que permite adelantar el reloj y ejecutar trabajos para la presentación. |
