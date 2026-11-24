---
inclusion: always
---

# Stack tecnológico

Rumbo es un **monolito**: un solo repositorio, una sola aplicación Node.js y una sola imagen Docker. El frontend y el backend viven en el mismo proyecto Astro, separados por carpetas (ver `architecture.md` y `conventions.md`).

## Resumen

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| Lenguaje | TypeScript (modo `strict`) | Un solo lenguaje en todo el proyecto. |
| Runtime | Node.js 24 LTS | Versión LTS activa. |
| Framework web | Astro (última versión estable) con salida `server` y adaptador `@astrojs/node` en modo `middleware` | SSR, rutas de API y Astro Actions en el mismo proyecto. El modo `middleware` permite montar Astro dentro de nuestro propio servidor y arrancar los trabajos en segundo plano en el mismo proceso. |
| Servidor HTTP | Express 5 (solo como contenedor de Astro y para el endpoint de salud) | Punto de entrada único (`servidor.ts`). |
| Islas interactivas | React 19 vía `@astrojs/react` | Necesario para el chat con streaming, el calendario con arrastrar y soltar, el mapa conceptual y la sesión de estudio. El resto de páginas son componentes `.astro` sin JavaScript. |
| Estilos | Tailwind CSS v4 (plugin `@tailwindcss/vite`) | Pedido por el equipo. |
| Base de datos | PostgreSQL 17 con extensión `pgvector` | Datos relacionales y vectores del RAG en el mismo motor. |
| ORM y migraciones | Drizzle ORM + drizzle-kit | Tipado fuerte, soporta `vector` y SQL directo cuando hace falta. |
| Validación | Zod | Entradas de Actions, variables de entorno y salidas de la IA. |
| Trabajos y cron | pg-boss | Cola y tareas programadas sobre el mismo PostgreSQL. No agrega infraestructura. |
| Fechas | `date-fns` v4 + `@date-fns/tz` | Cálculos de calendario en `America/Lima`. |
| IA (texto) | Claude en Amazon Bedrock: **Claude Haiku 5.5** mediante un perfil de inferencia entre regiones | Un solo modelo, rápido y barato, para chat, generación y análisis. El ID del modelo va en una variable de entorno. |
| IA (embeddings) | Amazon Titan Text Embeddings V2 (1024 dimensiones, normalizados) | Multilingüe, disponible en Bedrock, sin otro proveedor. |
| SDK de AWS | AWS SDK for JavaScript v3 (`@aws-sdk/client-bedrock-runtime`, `client-s3`, `s3-request-presigner`, `client-textract`, `client-sesv2`) | Cliente oficial. Para Bedrock se usa la API **Converse / ConverseStream**. |
| Lectura de documentos | `unpdf` (PDF por página), `jszip` + `fast-xml-parser` (PPTX por diapositiva), `mammoth` (DOCX), Amazon Textract (imágenes y PDFs escaneados) | Se conserva el número de página o diapositiva para las citas. |
| Archivos | Amazon S3 (bucket privado, subida con URL prefirmada) | Los documentos no pasan por el servidor al subirlos. |
| Correo | Amazon SES v2 | Servicio de correo simple de AWS. |
| UI auxiliar | `@xyflow/react` (mapa conceptual y camino visual), `@dnd-kit/core` (arrastrar sesiones), `recharts` (gráficos) | Librerías maduras para las tres vistas complejas. |
| Calidad | Biome (formato y lint), Vitest (pruebas unitarias del dominio) | Una sola herramienta de lint/formato. |
| Gestor de paquetes | pnpm | Rápido y con lockfile estricto. |

## Infraestructura en AWS

Región: **`us-east-1`** para todo (Bedrock, S3, Textract, SES, RDS, ECS). Perú no tiene región propia de AWS con todos estos servicios; usar una sola región evita tráfico entre regiones.

| Recurso | Servicio | Notas |
|---------|----------|-------|
| Aplicación | **Amazon ECS Express Mode** (Fargate + balanceador administrado) | AWS App Runner ya no acepta clientes nuevos desde el 30/04/2026 y AWS recomienda ECS Express Mode como reemplazo. Una sola tarea es suficiente para el hackathon. |
| Imagen | Amazon ECR | Imagen construida desde el `Dockerfile` del repo. |
| Base de datos | Amazon RDS for PostgreSQL 17, `db.t4g.micro`, con `pgvector` habilitado | Instancia única, sin réplica. |
| Archivos | Amazon S3 | Bloqueo de acceso público activo, cifrado SSE-S3, CORS solo para el dominio de la app. |
| Secretos | AWS Secrets Manager | Credenciales de la base de datos y secreto de firma de cookies. |
| Logs | Amazon CloudWatch Logs | Logs JSON de la aplicación. |
| Permisos | Rol de tarea de ECS con mínimo privilegio | Ver `security-privacy.md`. |
| IaC | AWS CDK en TypeScript, carpeta `infra/` | Opcional en el hackathon: si no hay tiempo, se documenta la creación manual en `infra/README.md`. |

### Pendientes antes de empezar

- Confirmar en la consola de Bedrock que la cuenta tiene acceso a Claude Haiku 5.5 y a Titan Text Embeddings V2 en `us-east-1`, y anotar el ID del perfil de inferencia en `BEDROCK_MODELO_TEXTO`.
- SES empieza en modo sandbox: solo envía a direcciones verificadas. Para la demo, verificar los correos del equipo o solicitar la salida del sandbox.

## Desarrollo local

- `docker compose up` levanta PostgreSQL con la imagen `pgvector/pgvector:pg17`.
- Los servicios de AWS (Bedrock, S3, Textract, SES) se usan reales con un perfil de credenciales de desarrollo y un bucket `rumbo-documentos-dev`.
- `pnpm dev` arranca Astro en modo desarrollo. `pnpm trabajos` arranca los trabajadores de pg-boss por separado durante el desarrollo.
- `pnpm semilla` carga los datos de la demo.

## Variables de entorno

Se validan con Zod al arrancar en `src/servidor/config.ts`. Si falta una, la app no arranca.

| Variable | Ejemplo |
|----------|---------|
| `DATABASE_URL` | `postgres://rumbo:rumbo@localhost:5432/rumbo` |
| `AWS_REGION` | `us-east-1` |
| `BEDROCK_MODELO_TEXTO` | ID del perfil de inferencia de Claude Haiku 5.5 |
| `BEDROCK_MODELO_EMBEDDINGS` | `amazon.titan-embed-text-v2:0` |
| `S3_BUCKET_DOCUMENTOS` | `rumbo-documentos-dev` |
| `SES_REMITENTE` | `Rumbo <hola@dominio-verificado>` |
| `SECRETO_COOKIES` | 32 bytes aleatorios en base64 |
| `URL_PUBLICA` | `https://rumbo.ejemplo.com` |
| `MODO_DEMO` | `true` habilita el reloj simulado y los atajos de demo |

## Lo que no se usa (y por qué)

- **Bedrock Knowledge Bases:** se descartó para controlar la división por página, las citas exactas y la búsqueda híbrida. Además, pgvector ya está en la base de datos.
- **Redis / SQS:** pg-boss cubre colas y cron con PostgreSQL.
- **Cognito u otra autenticación:** el MVP no tiene login (ver `product.md`).
- **Frameworks de agentes (LangChain, etc.):** las llamadas a Bedrock son directas y simples.
