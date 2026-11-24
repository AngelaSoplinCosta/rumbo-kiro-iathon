# Servicios de AWS en Rumbo

Región única para todo: **`us-east-1`**.

## Servicios que usamos actualmente (prototipo de la Kiro IAthon)

El estado actual son dos despliegues: una API serverless (`template.yaml`) y el prototipo web estático (`web/`).

| Servicio | Para qué lo usamos hoy |
|----------|------------------------|
| AWS Lambda | Toda la API corre en una sola función Python 3.12 (`src/app.py`). |
| Amazon API Gateway (HTTP API) | Expone las rutas públicas (`/health`, `/items`, `/cursos`, `/jobs`, etc.). |
| Amazon DynamoDB | Persistencia de items, cursos y jobs (tabla única `PAY_PER_REQUEST`). |
| Amazon Bedrock | IA generativa con la API Converse (Claude Haiku) para redactar el plan, el chat sobre documentos y detectar temas. |
| Amazon S3 | Hospeda el prototipo web (bucket privado) y guarda el artefacto de despliegue de SAM. |
| Amazon CloudFront | Sirve el sitio web con Origin Access Control (OAC) sobre el bucket privado. |
| AWS CloudFormation / SAM | Infraestructura de la API declarada en `template.yaml`. |
| AWS IAM | Rol de la Lambda con permisos mínimos (DynamoDB + `bedrock:InvokeModel`). |

## Servicios que deberíamos usar en el producto final

El producto final es un monolito Node.js (Astro) desplegado en contenedor, según `tech-stack.md`.

| Servicio | Para qué se usaría |
|----------|--------------------|
| Amazon ECS Express Mode (Fargate) | Corre la aplicación monolito (reemplaza Lambda; App Runner ya no acepta clientes nuevos). |
| Amazon ECR | Imagen Docker construida desde el `Dockerfile` del repo. |
| Amazon RDS for PostgreSQL 17 (+ pgvector) | Base de datos relacional y vectores del RAG en el mismo motor. |
| Amazon Bedrock | Claude Haiku 5.5 (texto, API Converse/ConverseStream) y Titan Text Embeddings V2 (embeddings). |
| Amazon S3 | Documentos subidos por el estudiante (bucket privado, subida con URL prefirmada). |
| Amazon Textract | Extracción de texto de imágenes y PDFs escaneados. |
| Amazon SES v2 | Envío de correos (notificaciones). |
| AWS Secrets Manager | Credenciales de la base de datos y secreto de firma de cookies. |
| Amazon CloudWatch Logs | Logs JSON de la aplicación. |
| AWS IAM | Rol de tarea de ECS con mínimo privilegio. |
| AWS CDK (TypeScript) | Infraestructura como código en `infra/` (opcional en el hackathon). |

## Diferencias clave

- **Cómputo:** hoy Lambda + API Gateway; en el producto final ECS Express Mode (Fargate) con un proceso Node.js de larga vida.
- **Datos:** hoy DynamoDB; en el producto final RDS PostgreSQL con pgvector.
- **IA:** hoy solo Bedrock para texto; en el producto final se suma Titan Embeddings V2 para el RAG, más Textract para documentos escaneados.
- **Servicios nuevos en el final:** ECR, RDS, Textract, SES, Secrets Manager y CloudWatch Logs.
