# Tareas — Rumbo (producto)

En orden. Cada tarea apunta a los requisitos de `requirements.md`. Las tareas de la API base están en `.kiro/specs/api-starter-kit/tasks.md`.

## Flujo central (ya construido)

- [x] 1. `POST /cursos` con varios PDFs, `GET /cursos`, `GET /cursos/{id}`; texto extraído en el navegador con pdf.js. (R1)
- [x] 2. Heurística de temas y planificador `generar_ruta` con simulacro final y modo rescate en `src/ruta.py`. (R3.3, R4)
- [x] 3. Detección de temas con Bedrock (`ia.detectar_temas_ia`) con validación de la salida JSON y respaldo a la heurística. (R3)
- [x] 4. `POST|PUT /cursos/{id}/documentos` para agregar y seleccionar documentos. (R5)
- [x] 5. Chat sobre los documentos con delimitadores y frase fija cuando no hay respuesta. (R6)
- [x] 6. Plan redactado por IA con reintentos, respaldo y 502. (R7)

## Validación y costos

- [x] 7. Crear `src/validacion.py`: tope de cuerpo, extensión `.pdf`, máximo 10 documentos, tope de texto por documento y curso, legibilidad, `minutosPorDia`, `fechaExamen` y tamaño final del ítem. Usarlo en `POST /cursos` y `POST|PUT /cursos/{id}/documentos`. (R2)
- [x] 8. Topes en `web/subir.html`: 10 PDFs y 20 MB por archivo. (R2.9)
- [x] 9. Crear `src/limites.py` con contadores atómicos por curso, IP y global; TTL `expira` en `ItemsTable`; variables `LIMITE_*` en `template.yaml`. (R12.1, R12.4)
- [x] 10. Reservar cupo en chat y plan después de validar (429) y en detección de temas (respaldo a heurística). (R12.2, R12.3, R6.4)
- [x] 11. `DefaultRouteSettings` de throttling en la HTTP API. (R12.5)
- [x] 12. Ocultar los contadores `limite#` en `GET /items`. (R12.6)

## Alerta temprana de abandono

- [x] 13. `riesgo.registrar_actividad` y `POST /cursos/{id}/actividad`. (R8)
- [x] 14. `riesgo.extraer_senales` y `riesgo.calcular_riesgo` con los cinco factores y niveles. (R9.1, R9.2)
- [x] 15. `riesgo.elegir_intervencion` con ritmos y mensajes sin culpa, sin repetir el mismo nivel dos días seguidos. (R9.3, R10.1–R10.4, R10.6, R10.7)
- [x] 16. `ruta.replanificar`: conserva lo completado, reparte lo pendiente desde hoy, sube `version` y arma el aviso. (R10.5)
- [x] 17. `GET|POST /cursos/{id}/riesgo` con `hoy` simulado acotado a ±60 días; guardar evaluación e historial. (R9.4, R9.5)
- [x] 18. Regla diaria de EventBridge (`RiesgoDiario`) y `_evaluar_todos`; `ritmo` en `GET /cursos`. (R11)
- [x] 19. Front: tarjeta "Tu ritmo" y botón "Completé mi sesión de hoy" en `espacio.html`; el panel de demo usa la API. (R13)

## Pruebas y documentación

- [x] 20. `tests/test_riesgo.py` (funciones puras, historia de Lucía) y casos nuevos en `tests/test_app.py` (validación, cupos, riesgo, evento programado). (R14)
- [x] 21. Documentar rutas y límites en `README.md` y el diseño de IA y riesgo en `design.md`. (R9–R12)
- [ ] 22. Desplegar con `sam deploy` y verificar en vivo: `GET /cursos/{id}/riesgo`, `POST /cursos/{id}/riesgo` con `hoy` adelantado, un 429 al bajar un cupo y la regla `RiesgoDiario` en EventBridge. (R9–R12)
