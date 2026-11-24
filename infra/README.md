# Infraestructura — Rumbo (Kiro IAthon)

Todo en la cuenta `000000000000`, región `us-east-1`. Dos despliegues independientes.

## 1. API serverless (Lambda + API Gateway + DynamoDB)

Definida en `template.yaml` con AWS SAM.

- **Stack:** `rumbo-iathon`
- **ApiUrl:** https://example.invalid
- **WebUrl:** https://example.invalid/app (la Lambda sirve `web/`, empaquetado como capa `WebLayer` en `/opt`)
- **teamId:** `T034` (parámetro `TeamId`, llega a la Lambda como `TEAM_ID`)

Rutas públicas:

| Método | Ruta | Para |
|--------|------|------|
| GET | `/health` | Insignia "API viva" |
| POST | `/items` | Insignia "Persistencia" |
| GET | `/items/{id}` | Insignia "Persistencia" |
| GET | `/items` | Insignia "Persistencia" |

### Redesplegar

```bash
sam deploy --template-file template.yaml --stack-name rumbo-iathon --region us-east-1 \
  --s3-bucket rumbo-iathon-deploy-000000000000 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides TeamId=T034 \
  --no-confirm-changeset --no-fail-on-empty-changeset
```

> Nota: el rol del entorno deniega `s3:PutBucketPublicAccessBlock`, por eso NO se usa
> `--resolve-s3` (falla al crear el bucket administrado de SAM). Se usa un bucket de
> despliegue propio: `rumbo-iathon-deploy-000000000000`.
> `sam build` se omite porque la función solo usa `boto3`, que ya viene en el runtime, y
> porque el entorno solo tiene Python 3.9 (falla la validación de `python3.12`).

## 2. Prototipo web (S3 privado + CloudFront con OAC)

- **Bucket:** `rumbo-iathon-web-000000000000` (privado, sin acceso público)
- **CloudFront:** distribución `DISTRIBUTION_ID`
- **URL:** https://example.invalid
- **Acceso:** Origin Access Control `E1AFOBJDHC6E0` + política de bucket que solo
  permite `s3:GetObject` a esta distribución (`infra/bucket-policy.json`). No se usa
  acceso público al bucket, porque el rol deniega `PutBucketPublicAccessBlock`.

### Actualizar el sitio

```bash
aws s3 sync web/ s3://rumbo-iathon-web-000000000000/ --delete
aws cloudfront create-invalidation --distribution-id DISTRIBUTION_ID --paths "/*"
```

## Limpieza

```bash
sam delete --stack-name rumbo-iathon --region us-east-1
aws cloudfront delete-distribution --id DISTRIBUTION_ID   # requiere deshabilitarla antes
aws s3 rb s3://rumbo-iathon-web-000000000000 --force
aws s3 rb s3://rumbo-iathon-deploy-000000000000 --force
```
