# Requisitos — API del starter kit

Parte de `CANVAS.md` y de la carta del track en `RETOS.md`. Define el contrato de la API serverless de respaldo del prototipo Rumbo para la Kiro IAthon. Todas las rutas son publicas y sin autenticacion.

## R1 — Salud de la API (insignia "API viva")

**Historia:** como verificador del portal, quiero un endpoint de salud publico para confirmar que la API del equipo esta viva.

Criterios de aceptacion:

1. CUANDO se hace `GET /health`, ENTONCES la respuesta es `200` con cuerpo JSON `{"status":"ok","team":"<TEAM_ID>"}`.
2. El campo `team` es exactamente el `teamId` publico del equipo (`T034`), que llega a la Lambda por la variable de entorno `TEAM_ID`, derivada del parametro `TeamId` de `template.yaml`.
3. La ruta responde sin ninguna cabecera de autenticacion.
4. El `content-type` de la respuesta es `application/json`.

## R2 — Crear item (insignia "Persistencia")

**Historia:** como verificador, quiero crear un item con un valor y recibir su id, para comprobar que la API persiste datos.

Criterios de aceptacion:

1. CUANDO se hace `POST /items` con cuerpo `{"value":"<nonce>"}`, ENTONCES la respuesta es `200` o `201` con JSON `{"id":"<id nuevo>","value":"<nonce>"}`.
2. El item se guarda en la tabla DynamoDB `ItemsTable`, cuyo nombre llega por la variable `TABLE_NAME`.
3. SI el cuerpo no trae `value`, ENTONCES la respuesta es `400` con un mensaje de error en JSON.

## R3 — Obtener item por id (insignia "Persistencia")

Criterios de aceptacion:

1. CUANDO se hace `GET /items/{id}` de un item existente, ENTONCES la respuesta es `200` con JSON `{"id":"<id>","value":"<nonce>"}`.
2. SI el item no existe, ENTONCES la respuesta es `404`.

## R4 — Listar items (insignia "Persistencia")

Criterios de aceptacion:

1. CUANDO se hace `GET /items`, ENTONCES la respuesta es `200` con un arreglo JSON de items o un objeto `{"items":[...]}`.
2. La lista incluye el item recien creado.
3. La lista devuelve hasta 100 items paginando el scan de DynamoDB; nunca se limita a la primera pagina.

## R5 — Rendimiento y formato

1. El verificador crea un item con un valor aleatorio y lo encuentra por id y en la lista en menos de 25 segundos.
2. Todas las respuestas usan `content-type: application/json`.

## R6 — Restricciones

1. Solo se usan datos simulados; nunca datos personales reales (nombres, correos, telefonos).
2. Solo se usan la cuenta de AWS del equipo y los servicios declarados en `template.yaml` (Lambda, API Gateway, DynamoDB). No hay sistemas externos.
3. Las rutas viven en `src/app.py` (funcion `handler`).

## R7 — Pruebas

1. Las pruebas locales corren con `python -m pytest -q tests` y cubren R1 a R4.
2. Las pruebas de `/items` usan una tabla falsa (monkeypatch de `TABLE`), sin tocar DynamoDB real.
