# Tareas — API del starter kit

En orden. Cada tarea apunta a los requisitos que cumple.

- [x] 1. Crear la estructura del proyecto SAM: `src/app.py`, `template.yaml`, `tests/`. (R6)
- [x] 2. Implementar `GET /health` que devuelve `{"status":"ok","team":<TEAM_ID>}` leyendo `TEAM_ID` del entorno. (R1)
- [x] 3. Definir en `template.yaml` el parametro `TeamId`, la tabla `ItemsTable`, la funcion Lambda con `TEAM_ID` y `TABLE_NAME`, el `DynamoDBCrudPolicy` y las rutas de HTTP API. (R1, R2, R6)
- [x] 4. Implementar `POST /items`: validar `value`, generar `id`, guardar en DynamoDB y responder 201. (R2)
- [x] 5. Implementar `GET /items/{id}`: devolver el item o 404. (R3)
- [x] 6. Implementar `GET /items` con paginacion del scan hasta 100 items. (R4)
- [x] 7. Asegurar `content-type: application/json` en todas las respuestas. (R5)
- [x] 8. Escribir `tests/test_health.py` y `tests/test_app.py` (tabla falsa) y `conftest.py`. (R7)
- [x] 9. Correr `python -m pytest -q tests` y dejar todo en verde. (R7)
- [x] 10. Instalar SAM CLI. (`sam build` se omite: la funcion solo usa boto3, incluido en el runtime; se despliega el codigo fuente directo). (R6)
- [x] 11. Desplegar con `sam deploy ... --parameter-overrides TeamId=T034`. Output `ApiUrl = https://example.invalid`. (R1-R6)
- [x] 12. Verificado en vivo: `/health` da `{"status":"ok","team":"T034"}` y el ciclo `POST /items` + `GET /items/{id}` + `GET /items` funciona con content-type JSON. (R1-R5)
- [x] 13. Flujo central de cursos: `POST /cursos` (varios PDFs), `GET /cursos`, `GET /cursos/{id}`, `POST /cursos/{id}/documentos` (agrega y regenera la ruta). Front: subir varios PDFs y agregar mas dentro del espacio.
- [x] 14. **GenAI con proposito** (Bedrock Converse): `POST /cursos/{id}/plan` redacta el plan de estudio del temario+ruta recien generados. Modulo `src/ia.py` con prompt contextual (tono Rumbo, sin culpa, limite de longitud), validacion 400, reintentos ante ThrottlingException, respaldo si el modelo no responde y 502 en errores no recuperables. `MODEL_ID` en `template.yaml`, permiso `bedrock:InvokeModel`. Front: boton "Generar mi plan con IA" en el espacio con loading. Pruebas con Bedrock simulado. Verificado en vivo.
- [x] 15. **Asincrono o agente**: `POST /jobs` responde 202 con `{jobId}` y guarda el trabajo (readyAt = ahora + 2s); `GET /jobs/{jobId}` devuelve `queued` y luego `done` con el `input` invertido. Resuelto al leer. Pruebas con reloj congelado. Verificado en vivo (queued -> done antes de 12s).
- [x] 16. **Retos de Halloween**: `GET /pumpkin?nonce=` (palabra al reves + team), `POST /exorcise` (sin duplicados, orden de primera aparicion), `POST /conjuro` (dias de la semana en espanol). Steering `halloween.md` y hook `validar-contrato-api.kiro.hook`. Pruebas y verificacion en vivo.
- [x] 17. Front: persistir cursos reales desde la API en Inicio y Espacios; se quitaron los cursos mockeados y queda solo un espacio "Demo" claramente marcado.
- [ ] 18. Pegar `ApiUrl` (sin barra final) en Perfil del equipo del portal, describir la funcionalidad GenAI y pulsar "Verificar ahora" en cada insignia. (manual del usuario)

> Nota de despliegue: el rol del entorno tiene un deny sobre `s3:PutBucketPublicAccessBlock`, asi que `--resolve-s3` falla. Se usa un bucket de despliegue propio: `--s3-bucket rumbo-iathon-deploy-000000000000`.
