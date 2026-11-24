---
inclusion: always
---

# Producto: Rumbo

> Fuente original: `contexto/rumbo-idea-principal.md` y `contexto/rumbo-funcionalidades.md`.
> Este archivo resume el producto y fija las decisiones de alcance para el hackathon.

## Qué es

Rumbo es una aplicación web que actúa como compañero de estudio contra el abandono. El estudiante sube los materiales de su curso (PDF, PPTX, DOCX, imágenes de apuntes) y la fecha de su examen. Rumbo:

1. Extrae los temas del curso **solo desde sus documentos** (RAG con citas).
2. Arma una ruta de estudio día por día hasta el examen, según su disponibilidad.
3. Guía una sesión diaria con material citado, práctica y flashcards con repetición espaciada.
4. Replanifica cuando el estudiante se atrasa y activa un modo rescate si el tiempo no alcanza.
5. Calcula cada día un nivel de riesgo de abandono y responde con ayudas graduales.
6. Consolida lo aprendido con un resumen diario y una síntesis semanal con mapa conceptual.
7. Motiva en dos capas separadas: gamificación personal (XP, rachas, insignias) y social (amigos, rutas compartidas, ligas).

## Usuarios

- Estudiantes universitarios y de institutos en Perú con parciales o finales.
- Postulantes a exámenes de admisión.
- Personas que preparan certificaciones.
- La vista docente queda fuera del hackathon (F3).

## Principios de producto

Estos principios se aplican a todas las funcionalidades y a todos los textos generados por la IA:

1. **Todo sale de los documentos del estudiante.** Cada respuesta, pregunta, flashcard y resumen cita el documento y la página (o diapositiva) de origen. Si algo no está en los documentos, Rumbo lo dice claramente y no inventa.
2. **Sin culpa.** Los mensajes hablan de lo que se puede hacer hoy, no de lo que faltó. Ejemplo: "Con 30 min hoy recuperas el ritmo para el jueves". Nunca: "Llevas 3 días sin estudiar".
3. **Una acción principal.** La pantalla de inicio siempre muestra "Tu sesión de hoy" con su duración estimada.
4. **El plan se adapta.** Las tareas atrasadas no se acumulan: la ruta se reorganiza.
5. **Privado por defecto.** Los documentos son privados. Compartir una ruta no comparte documentos salvo permiso explícito. El estudiante controla qué ven sus amigos.
6. **Competencia sana.** El ranking es por ligas pequeñas, se reinicia cada semana, mide práctica real y permite participar en modo anónimo.

## Decisiones de alcance para el hackathon

| Tema | Decisión |
|------|----------|
| Plataforma | Solo web (responsive, usable en celular). |
| Autenticación | **Sin login.** Se usa un "perfil ligero": nombre y nombre de usuario, identificado por una cookie con un token aleatorio. Reemplaza el registro con correo y Google del documento de funcionalidades. Ver `security-privacy.md`. |
| Correo | Opcional en el perfil, solo para enviar notificaciones por correo. |
| Zona horaria | Única: `America/Lima`. |
| Idioma | Todo en español: interfaz, documentación, contenido generado y nombres en el código. |
| Prioridades | Se implementa lo marcado **[MVP]**. Lo marcado [F2] y [F3] queda fuera, salvo que se indique otra cosa en `sdd-features.md`. |
| Social | Amigos, rutas compartidas, copia de rutas y ranking por ligas **sí** entran. Compañero de estudio y grupos/foros (F2) no entran. |
| Formatos | PDF (con texto o escaneado), PPTX, DOCX, PNG y JPG. Los formatos antiguos `.ppt` y `.doc` no se aceptan: se pide convertirlos. |

## Historia de demo

La demo sigue el ejemplo de Lucía (ver `contexto/rumbo-idea-principal.md`):

1. Lucía crea el espacio "Física I", con examen en 10 días, sube 4 PDFs y el sílabo y declara 1 h diaria.
2. Rumbo detecta 9 temas, ella ajusta el temario y responde un diagnóstico corto.
3. Rumbo genera la ruta y ella la ve en el camino visual y en el calendario.
4. Hace su sesión de hoy, pregunta una duda al asistente y recibe la respuesta con cita.
5. Comparte la ruta con 3 amigos, que la copian y forman una liga.
6. Se simulan 3 días sin actividad (el documento original dice 2, pero la insignia "Volví" exige 3 o más): el riesgo sube a medio, Rumbo propone la sesión de 5 minutos, reorganiza la ruta y una amiga le envía un empujón.
7. Lucía vuelve y gana la insignia "Volví".
8. La síntesis semanal muestra "Dinámica" en rojo y el plan de refuerzo la prioriza.

Para la demo se necesita un script de datos semilla y una forma de simular el paso de los días (ver `sdd-features.md`, spec 01).

## Fuera de alcance

- Login con correo/Google, recuperación de contraseña.
- App móvil nativa, modo sin conexión, lectura en voz alta.
- WhatsApp, Google Calendar, enlaces web y videos como fuente, exámenes pasados.
- Compañero de estudio emparejado, grupos, foros, metas grupales, ascenso/descenso de ligas.
- Recompensas cosméticas, vitrina de logros, preparación estimada.
- Vista docente.
