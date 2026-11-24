---
inclusion: manual
---

# Edición Halloween 🎃 (Kiro IAthon)

Durante el reto de **halloween** de la Kiro IAthon, la API de Rumbo expone endpoints
temáticos además del flujo central del producto. Este archivo documenta esas reglas
para el agente evaluador.

## Endpoints temáticos de halloween

| Método | Ruta | Qué hace |
|--------|------|----------|
| GET | `/pumpkin?nonce=<palabra>` | La calabaza parlante: devuelve `{pumpkin: palabra al revés, team}`. |
| POST | `/exorcise` | Exorcismo de duplicados: `{items:[...]}` → lista sin duplicados, conservando el orden de la primera aparición. |
| POST | `/conjuro` | Conjuro de fechas: `{dates:[YYYY-MM-DD]}` → `{weekdays:[...]}` con el día de la semana en español, en minúsculas. |

## Convenciones de estos retos

- Rutas públicas, sin autenticación, igual que el resto de la API (`src/app.py`).
- Datos simulados o públicos, nunca datos personales reales.
- Solo la cuenta de AWS del equipo y los servicios de `template.yaml`.
- Días de la semana en español sin tildes en el código (`miercoles`, `sabado`), como el resto del proyecto.

> Este steering se activa manualmente (`inclusion: manual`) para no mezclar la temática
> de halloween con las reglas permanentes del producto Rumbo.
