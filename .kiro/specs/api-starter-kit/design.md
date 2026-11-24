# Diseño — API del starter kit

## Arquitectura minima en AWS

La API es serverless y vive en la cuenta del equipo, region `us-east-1`. Tres servicios, todos declarados en `template.yaml`:

```
Cliente / verificador del portal
        |
        v
  API Gateway (HTTP API)   rutas publicas, sin autorizador
        |
        v
  AWS Lambda (Python 3.12)  funcion handler en src/app.py
        |
        v
  Amazon DynamoDB (ItemsTable)  clave de particion: id (String)
```

- **API Gateway (HTTP API):** expone `/health`, `/items` y `/items/{id}`. Sin autorizador, por eso las rutas son publicas. El payload que recibe la Lambda es el formato v2.
- **Lambda:** una sola funcion (`ApiFunction`) con un router propio en `handler` que despacha por metodo y ruta. Recibe por entorno `TEAM_ID` (del parametro `TeamId`) y `TABLE_NAME` (del recurso `ItemsTable`).
- **DynamoDB:** tabla `ItemsTable` en modo `PAY_PER_REQUEST` (sin aprovisionar capacidad, barato para el hackathon). La Lambda tiene permiso solo sobre esta tabla (`DynamoDBCrudPolicy`), siguiendo minimo privilegio.

## Decisiones

- **Sin framework web.** El router manual mantiene el paquete pequeno y arranca rapido en Lambda; `boto3` ya viene en el runtime, asi que no hay dependencias que empaquetar.
- **Lectura diferida de la tabla.** `app.TABLE` se crea la primera vez que se usa, para que los tests reemplacen esa referencia con una tabla falsa sin conectarse a AWS.
- **`id` generado en la Lambda** con `uuid4().hex`, para no depender de que el cliente lo envie.
- **Listado con paginacion.** `GET /items` repite el `scan` siguiendo `LastEvaluatedKey` hasta juntar 100 items; nunca devuelve solo la primera pagina.
- **Compatibilidad de payload.** `handler` entiende tanto HTTP API v2 como REST v1, por si el tipo de API cambia.

## Contrato de respuestas

| Ruta | Metodo | Exito | Cuerpo |
|------|--------|-------|--------|
| `/health` | GET | 200 | `{"status":"ok","team":"T034"}` |
| `/items` | POST | 201 | `{"id":"...","value":"..."}` |
| `/items/{id}` | GET | 200 / 404 | `{"id":"...","value":"..."}` |
| `/items` | GET | 200 | `{"items":[...]}` |

Toda respuesta usa `content-type: application/json` y CORS abierto (`access-control-allow-origin: *`).

## Despliegue

Con AWS SAM:

```
sam build
sam deploy --stack-name rumbo-iathon --region us-east-1 \
  --resolve-s3 --capabilities CAPABILITY_IAM \
  --parameter-overrides TeamId=T034 \
  --no-confirm-changeset --no-fail-on-empty-changeset
```

El Output `ApiUrl` es la URL base. El `teamId` entra solo por `--parameter-overrides`, nunca hardcodeado.

## Pruebas

- `tests/test_health.py` cubre R1 (health con el team correcto, ruta publica).
- `tests/test_app.py` cubre R2 a R4 con una tabla falsa en memoria (monkeypatch de `app.TABLE`).
- `tests/conftest.py` agrega `src/` al path de import.
- Local: `python -m pytest -q tests`. Tras desplegar: `curl -s <ApiUrl>/health`.
