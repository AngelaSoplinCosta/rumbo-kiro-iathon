---
inclusion: always
---

# Convenciones

## Idioma

Todo el proyecto está en español: interfaz, documentación, mensajes de error, prompts, commits **y nombres en el código**.

- Las palabras reservadas del lenguaje y las APIs de librerías se quedan como son (`async`, `useState`, `defineAction`).
- Los identificadores **no usan tildes ni ñ**: `sesion`, `pagina`, `anio`, `contrasena`, `diagnostico`. Los textos visibles sí las usan.
- Se usa el mismo término para el mismo concepto en todo el código (ver `glossary.md`). Ejemplo: siempre `espacio`, nunca `curso` ni `workspace` para la entidad.

## Nombres

| Elemento | Formato | Ejemplo |
|----------|---------|---------|
| Archivos TS y carpetas | kebab-case | `generar-ruta.ts`, `modulos/rutas/` |
| Componentes Astro y React | PascalCase | `CaminoVisual.tsx`, `TarjetaSesion.astro` |
| Variables y funciones | camelCase | `fechaExamen`, `calcularRiesgo()` |
| Tipos e interfaces | PascalCase | `SesionPlanificada`, `NivelRiesgo` |
| Constantes globales | MAYUSCULAS_CON_GUION | `LIMITE_NOTIFICACIONES_DIA` |
| Tablas y columnas | snake_case, tabla en singular | `sesion_planificada.fecha_programada` |
| Enums de BD y valores de estado | snake_case en minúsculas | `'en_curso'`, `'modo_rescate'` |
| Trabajos de pg-boss | kebab-case, verbo primero | `procesar-documento`, `calcular-riesgo` |
| Eventos internos | `modulo.hecho_en_pasado` | `sesion.completada`, `respuesta.registrada` |
| Actions | `modulo.verbo` | `rutas.regenerar`, `social.enviarEmpujon` |

Las funciones empiezan con verbo en infinitivo: `obtenerRuta`, `crearEspacio`, `marcarCompletada`. Los booleanos empiezan con `es`, `tiene` o `puede`: `esMinima`, `tieneDocumentos`.

## Estructura de carpetas

```
/
├── contexto/                     # Documentos originales de la idea
├── .kiro/steering/               # Este conjunto de documentos
├── .kiro/specs/                  # Specs del SDD
├── infra/                        # AWS CDK (opcional) y README de despliegue
├── drizzle/                      # Migraciones SQL generadas
├── scripts/
│   └── semilla.ts                # Datos de la demo
├── servidor.ts                   # Entrada Node: Express + Astro + pg-boss
├── Dockerfile
├── docker-compose.yml
└── src/
    ├── actions/
    │   ├── index.ts              # Exporta `server` con todos los grupos
    │   └── <modulo>.ts
    ├── pages/
    │   ├── index.astro           # Inicio: "Tu sesión de hoy"
    │   ├── espacios/...
    │   ├── demo.astro            # Solo con MODO_DEMO
    │   └── api/                  # Solo SSE, prefirmado y salud
    ├── layouts/
    ├── componentes/              # Componentes .astro sin JS
    ├── islas/                    # Componentes React interactivos
    ├── estilos/global.css        # @import "tailwindcss" y tokens @theme
    ├── middleware.ts             # Resuelve el perfil desde la cookie
    └── servidor/
        ├── config.ts
        ├── reloj.ts
        ├── eventos.ts
        ├── errores.ts
        ├── db/
        │   ├── cliente.ts
        │   └── esquema/<modulo>.ts
        ├── dominio/              # Funciones puras + pruebas *.test.ts
        ├── ia/
        │   ├── bedrock.ts
        │   ├── embeddings.ts
        │   ├── busqueda.ts
        │   └── prompts/<caso>.ts
        ├── adaptadores/          # s3.ts, textract.ts, ses.ts
        ├── trabajos/             # registro.ts y un archivo por trabajo
        └── modulos/<modulo>/
            ├── servicio.ts
            ├── repositorio.ts
            ├── esquemas.ts       # Zod de entrada y salida
            └── tipos.ts
```

## TypeScript

- `strict: true`, sin `any`. Si un valor es desconocido, se usa `unknown` y se valida con Zod.
- Los tipos de las tablas se infieren de Drizzle (`typeof tabla.$inferSelect`). No se duplican a mano.
- Las fechas de calendario (sin hora) se manejan como texto `YYYY-MM-DD` (tipo `FechaISO`) y en la BD como `date`. Los instantes se guardan como `timestamptz`.
- Las duraciones siempre en **minutos** enteros.
- Los porcentajes y puntajes de dominio se guardan como número entre 0 y 1. Se convierten a % solo en la UI.
- IDs: `uuid` generados por PostgreSQL (`gen_random_uuid()`).
- Imports con alias `@/` para `src/`.

## Backend

- Toda entrada de usuario se valida con Zod en la Action o el endpoint.
- Cada servicio recibe `usuarioId` explícitamente y verifica que el recurso le pertenece (o que está compartido con él) antes de leer o modificar. Ver `security-privacy.md`.
- Las operaciones que tocan varias tablas usan `db.transaction`.
- Nada de lógica de negocio en el SQL (triggers, funciones). La única excepción son los índices y la búsqueda vectorial/texto completo.
- Las funciones del dominio no tienen efectos secundarios y reciben la fecha actual por parámetro.
- Los textos que ve el usuario viven junto a su módulo en `textos.ts` cuando se reutilizan, o en el componente si son únicos. No hay sistema de i18n.

## Frontend

- Por defecto, componentes `.astro` renderizados en el servidor. Se usa una isla React solo si hay interacción que lo justifique.
- Las islas usan `client:load` si son lo principal de la pantalla y `client:visible` en el resto.
- Las islas llaman a las Actions con `import { actions } from 'astro:actions'`.
- Tailwind v4: los colores del producto se definen como tokens en `@theme` dentro de `global.css` (ver `ux.md`). No se escriben colores hex sueltos en los componentes.
- Diseño mobile-first. Toda pantalla debe funcionar a 360 px de ancho.
- Accesibilidad mínima: contraste AA, foco visible, botones con texto o `aria-label`, los colores de estado siempre acompañados de ícono o texto.

## Base de datos

- Una migración por cambio, generada con `drizzle-kit generate` y revisada antes de aplicarse.
- Toda tabla tiene `id`, `creado_en` y, si se modifica, `actualizado_en`.
- Las claves foráneas hacia `usuario` usan `ON DELETE CASCADE` para que eliminar la cuenta borre todo.
- Índices obligatorios: claves foráneas, `(usuario_id, fecha)` en tablas por día, HNSW en `fragmento.embedding`, GIN en `fragmento.texto_busqueda`.

## Pruebas

- Pruebas unitarias con Vitest para todo `src/servidor/dominio/` (planificador, SM-2, riesgo, rachas, XP, ligas). Son funciones puras y son el corazón del producto.
- Los archivos de prueba van junto al código: `planificador.test.ts`.
- La IA no se prueba con llamadas reales en CI. Las funciones que validan la salida del modelo sí se prueban con respuestas de ejemplo.
- `pnpm verificar` ejecuta `biome check`, `tsc --noEmit` y `vitest run`.

## Git

- Rama principal `main`. Ramas por spec: `spec/05-ruta-aprendizaje`.
- Commits con formato Conventional Commits y descripción en español: `feat(rutas): agrega replanificación por atraso`, `fix(documentos): conserva el número de diapositiva`.
- Tipos: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
- No se suben secretos ni archivos `.env`. Se mantiene `.env.ejemplo` actualizado.
