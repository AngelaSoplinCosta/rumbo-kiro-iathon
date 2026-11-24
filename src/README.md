# Backend del prototipo

Los módulos Python implementan la lógica de la API diseñada para AWS Lambda. La infraestructura se describe en [`template.yaml`](../template.yaml).

| Archivo | Responsabilidad |
| --- | --- |
| `app.py` | Entrada y enrutamiento de solicitudes. |
| `ruta.py` | Planificación de la ruta de estudio. |
| `ia.py` | Operaciones de IA basadas en Amazon Bedrock. |
| `riesgo.py` | Señales e intervenciones de seguimiento. |
| `validacion.py` | Validación de entradas. |
| `limites.py` | Controles de uso. |

La presencia de estos módulos no acredita un despliegue activo ni una integración completa con la interfaz. Antes de usar datos reales se requiere revisar autenticación, aislamiento, validación de fuentes y configuración de infraestructura.
