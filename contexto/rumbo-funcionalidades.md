# Rumbo — Funcionalidades

> Lista de lo que la plataforma debe hacer, organizada por módulo.
> Prioridad: **[MVP]** imprescindible para la primera versión · **[F2]** segunda fase · **[F3]** a futuro.

---

## 1. Cuenta y perfil

- **[MVP]** Registro e inicio de sesión (correo y Google).
- **[MVP]** Perfil con nombre, foto/avatar y carrera o institución.
- **[MVP]** Configurar la disponibilidad semanal de estudio (ej. 1 h entre semana, 3 h los sábados).
- **[MVP]** Configurar el horario preferido de estudio y el horario de silencio para notificaciones.
- **[F2]** Preferencias de privacidad: perfil público/privado, aparecer o no en rankings.

---

## 2. Espacios de estudio (curso o examen)

- **[MVP]** Crear un espacio por curso o examen con nombre y **fecha del examen**.
- **[MVP]** Subir documentos: PDF, presentaciones, documentos de texto e imágenes de apuntes.
- **[MVP]** Subir el sílabo del curso (opcional) para guiar el temario.
- **[F2]** Agregar enlaces web y videos como fuente.
- **[F2]** Subir exámenes pasados para imitar el formato real.
- **[MVP]** Ver, renombrar y eliminar documentos del espacio.
- **[MVP]** Varios espacios activos a la vez (ej. 3 cursos en el mismo ciclo).

---

## 3. Asistente basado en tus documentos

- **[MVP]** Chat para hacer preguntas sobre el contenido del curso.
- **[MVP]** Cada respuesta muestra **de qué documento y página** salió.
- **[MVP]** Si la respuesta no está en los documentos, el asistente lo dice claramente.
- **[MVP]** Pedir explicaciones más simples, ejemplos o analogías.
- **[MVP]** Generar a pedido: cuestionarios, flashcards y resúmenes de un tema.
- **[MVP]** Botón "reportar error" en respuestas, preguntas y flashcards.
- **[F2]** Lectura en voz alta de respuestas y resúmenes.

---

## 4. Ruta de aprendizaje

- **[MVP]** Detectar automáticamente los **temas y subtemas** del curso a partir de los documentos.
- **[MVP]** Ordenar los temas según sus prerrequisitos.
- **[MVP]** Permitir al estudiante revisar y ajustar el temario detectado (agregar, quitar, reordenar).
- **[MVP]** **Diagnóstico inicial** opcional (5–10 preguntas) para saltar lo que ya sabe.
- **[MVP]** Generar la ruta **día por día** hasta la fecha del examen según su disponibilidad.
- **[MVP]** Incluir en la ruta:
  - días de repaso de temas anteriores,
  - un margen para imprevistos,
  - simulacros en los últimos días.
- **[MVP]** **Replanificación automática** cuando el estudiante se atrasa o adelanta.
- **[MVP]** **Modo rescate:** si ya no alcanza el tiempo, prioriza los temas más importantes.
- **[MVP]** Cambiar la fecha del examen y regenerar la ruta.
- **[MVP]** Ver la ruta como un camino visual con los temas completados, en curso y bloqueados.

---

## 5. Sesión de estudio diaria

- **[MVP]** Pantalla de inicio con una acción principal: **"Tu sesión de hoy"** con duración estimada.
- **[MVP]** Cada sesión incluye:
  - un objetivo claro,
  - un fragmento o resumen del material (con cita),
  - práctica (preguntas y/o flashcards),
  - una autoevaluación final.
- **[MVP]** Flashcards con **repetición espaciada** (las difíciles reaparecen antes).
- **[MVP]** Asistente disponible durante la sesión para resolver dudas.
- **[MVP]** **Sesión mínima de 5 minutos** para días con poco tiempo, que mantiene la racha.
- **[MVP]** Pausar y retomar una sesión.
- **[F2]** Descargar la sesión del día para estudiar sin conexión.

---

## 6. Calendario

- **[MVP]** Vista mensual y semanal con sesiones planificadas, completadas, pendientes y el día del examen.
- **[MVP]** Código de colores por estado y por espacio (curso).
- **[MVP]** Mover una sesión a otro día arrastrándola.
- **[MVP]** Indicador de avance real vs. planificado.
- **[F2]** Sincronizar con Google Calendar u otros calendarios.

---

## 7. Notificaciones y alertas

- **[MVP]** Recordatorio diario a la hora preferida.
- **[MVP]** Aviso de resumen diario y síntesis semanal disponibles.
- **[MVP]** Alertas de cuenta regresiva al examen (ej. 7 días, 3 días, 1 día).
- **[MVP]** Alertas según el **nivel de riesgo** (ver módulo 8).
- **[MVP]** Límite de notificaciones al día y respeto del horario de silencio.
- **[MVP]** Notificaciones en la web/app y por correo.
- **[F2]** Notificaciones por WhatsApp.

---

## 8. Detección de riesgo de abandono

- **[MVP]** Calcular cada día un nivel de riesgo por estudiante y por ruta, según:
  - días sin actividad,
  - atraso respecto al plan,
  - caída en el porcentaje de aciertos,
  - sesiones dejadas a la mitad,
  - cercanía del examen con mucho temario pendiente.
- **[MVP]** Intervenciones graduales:

| Nivel | Qué hace Rumbo |
|-------|----------------|
| 🟢 Bajo | Recordatorio normal |
| 🟡 Medio | Propone la sesión mínima de 5 min y reorganiza la ruta |
| 🟠 Alto | Activa el modo rescate y, si el estudiante lo permite, avisa a su compañero de estudio |
| 🔴 Crítico | Mensaje empático para replantear la meta, ajustar la disponibilidad o pedir ayuda |

- **[MVP]** Mensajes con tono positivo y sin culpa (ej. "Con 30 min hoy recuperas el ritmo para el jueves").
- **[MVP]** El estudiante ve su propio indicador de "ritmo" de forma sencilla.

---

## 9. Dashboard de aprendizaje

### Resumen diario (cada mañana, ~2 minutos)
- **[MVP]** Qué aprendiste ayer: 3–5 ideas clave con su fuente.
- **[MVP]** En qué fallaste: preguntas incorrectas y su explicación.
- **[MVP]** 3 flashcards de repaso rápido.
- **[MVP]** Qué toca hoy y cuántos días faltan para el examen.

### Síntesis semanal (cada domingo)
- **[MVP]** **Mapa conceptual** de los temas vistos en la semana, con colores:
  🟢 dominado · 🟡 en progreso · 🔴 débil · ⚪ no visto.
- **[MVP]** Al tocar un tema del mapa: resumen y práctica dirigida.
- **[MVP]** Mini simulacro semanal de 10 preguntas mezcladas.
- **[MVP]** Gráfico de avance real vs. planificado.
- **[MVP]** Plan de refuerzo para la semana siguiente basado en los temas débiles.
- **[F2]** Descargar o compartir el mapa conceptual.

### Vista general
- **[MVP]** Porcentaje de la ruta completado por cada espacio.
- **[MVP]** Dominio por tema.
- **[F2]** **Preparación estimada** para el examen (ej. "Estás 68 % listo").

---

## 10. Gamificación personal (separada del ranking)

- **[MVP]** **XP** por sesiones completadas, respuestas correctas y repasos.
- **[MVP]** **Rachas** de días estudiados.
- **[MVP]** **Comodines de racha** (1 por semana) para no perder la racha por un mal día.
- **[MVP]** **Insignias por hitos**, por ejemplo:
  - primer tema dominado,
  - 7 días seguidos,
  - primer simulacro,
  - **"Volví"**: regresar después de 3 o más días sin estudiar.
- **[MVP]** **Niveles** por ruta, visibles en el camino de aprendizaje.
- **[MVP]** **Recompensa final** al completar la ruta antes del examen.
- **[F2]** Recompensas cosméticas: avatares, temas visuales y marcos de perfil.
- **[F2]** Vitrina de logros en el perfil.

---

## 11. Amigos y comunidades

### Amigos
- **[MVP]** Agregar amigos por nombre de usuario o enlace de invitación.
- **[MVP]** Ver si tus amigos estudiaron hoy (si ellos lo permiten).
- **[MVP]** Enviar un "empujón" o mensaje de ánimo.
- **[F2]** Agregar amigos por código QR.

### Compartir rutas
- **[MVP]** Compartir una ruta de aprendizaje con amigos mediante un enlace.
- **[MVP]** Copiar la ruta de otra persona para seguirla.
- **[MVP]** Elegir si se comparten también los documentos o solo la estructura y las preguntas.

### Compañero de estudio
- **[F2]** Emparejar a dos personas que siguen la misma ruta.
- **[F2]** Cada uno ve el avance del otro y recibe avisos si su compañero está en riesgo.

### Comunidades y grupos
- **[F2]** Crear grupos por curso, universidad o examen (ej. "Admisión 2027").
- **[F2]** Foro de dudas por tema dentro del grupo.
- **[F2]** **Metas grupales** (ej. "50 sesiones entre todos esta semana") con recompensa compartida.

---

## 12. Ranking (separado de la gamificación personal)

- **[MVP]** Ranking dentro de cada ruta compartida.
- **[MVP]** Dos tipos de ranking:
  - **Avance:** porcentaje de la ruta completado.
  - **Constancia:** días activos en la semana.
- **[MVP]** **Ligas pequeñas** (10–30 personas) en lugar de un ranking global.
- **[MVP]** **Reinicio semanal** para que todos tengan oportunidad de subir.
- **[MVP]** Puntaje basado en práctica real (preguntas respondidas), no en tiempo con la app abierta.
- **[MVP]** Opción de participar en **modo anónimo** u ocultarse del ranking.
- **[F2]** Ascenso y descenso entre ligas.

---

## 13. Privacidad y confianza

- **[MVP]** Documentos privados por defecto.
- **[MVP]** Compartir una ruta no comparte los documentos, salvo permiso explícito.
- **[MVP]** Control sobre qué ven los amigos (avance, actividad, ranking).
- **[MVP]** Eliminar la cuenta y todos los datos.

---

## 14. Vista docente / tutor *(a futuro)*

- **[F3]** El docente crea la ruta oficial del curso y la comparte con su salón.
- **[F3]** Tablero con el avance y el nivel de riesgo del grupo.
- **[F3]** Enviar mensajes o refuerzos a los estudiantes en riesgo.

---

## Resumen de prioridades del MVP

1. Espacios con documentos y asistente con citas.
2. Ruta de aprendizaje automática con replanificación y modo rescate.
3. Sesión diaria con práctica y repetición espaciada.
4. Calendario y notificaciones.
5. Detección de riesgo con intervenciones graduales.
6. Resumen diario y mapa conceptual semanal.
7. Gamificación personal (XP, rachas, comodines, insignias).
8. Amigos, rutas compartidas y ranking por ligas.
