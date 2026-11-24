---
inclusion: always
---

# Convenciones del proyecto (Kiro IAthon)

Rumbo: companero de estudio contra el abandono. Este proyecto tiene dos partes.

## Partes

1. **Prototipo web estatico y clickeable** en `web/`: HTML + CSS + JS, sin backend. Muestra la historia de Lucia con datos simulados. Se despliega en S3 + CloudFront.
2. **API serverless** en `src/app.py` + `template.yaml`: Lambda + API Gateway (HTTP API) + DynamoDB. Rutas publicas `/health` e `/items`.

## Stack

- API: Python 3.12, solo `boto3` (ya viene en Lambda). Sin frameworks web. Despliegue con AWS SAM en `us-east-1`.
- Web: HTML/CSS/JS plano. Sin build. Mobile-first, funciona a 360 px.
- Infra declarada solo en `template.yaml` (API) y comandos de S3/CloudFront (web).

## Nombres y estilo

- Codigo y textos en espanol. Identificadores sin tildes ni enie (`sesion`, `anio`).
- Python: `snake_case` para funciones y variables; funciones privadas con guion bajo inicial.
- Commits en espanol con Conventional Commits (`feat`, `fix`, `docs`).

## Como probar

- API local: `python -m pytest -q tests` (usa tabla falsa, no toca AWS).
- API desplegada: `curl -s <ApiUrl>/health` debe dar `{"status":"ok","team":"T034"}`.
- Despliegue: `sam build && sam deploy --stack-name rumbo-iathon --region us-east-1 --resolve-s3 --capabilities CAPABILITY_IAM --parameter-overrides TeamId=T034 --no-confirm-changeset --no-fail-on-empty-changeset`.

## Que NO hacer

- No usar datos personales reales (nombres, correos, telefonos): solo simulados o publicos.
- No conectar sistemas externos: solo la cuenta de AWS del equipo y los servicios de `template.yaml`.
- No hardcodear el `teamId` en el codigo: entra por el parametro `TeamId`.
- No agregar autenticacion a `/health` ni a `/items`: son rutas publicas por contrato.
