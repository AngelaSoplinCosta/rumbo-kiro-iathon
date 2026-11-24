# Rumbo — compañero de estudio

Rumbo es un prototipo desarrollado por el equipo **T034 · Los más Kiros** para el Kiro IAThon de AWS, en el reto «Compañero de estudio contra el abandono».

## Problema y propuesta

El proyecto explora cómo ayudar a estudiantes a organizar su aprendizaje a partir de materiales de estudio, una fecha objetivo y el seguimiento de su avance.

## Equipo

Proyecto colaborativo de Angela Soplin Costa, Ruth Nadiezhda Araujo Carhuancho, Riggel Rojas, Jorge Quispe Bendezú, Ricardo Quispe Fernandez y Geraldo Emilio Sosa Sosa. Angela participó en mejoras de la propuesta, gamificación, flujo de experiencia de usuario (UX) y pruebas. La distribución detallada de las contribuciones del resto del equipo está pendiente de precisar.

## Alcance del entregable

La documentación del proyecto describe una interfaz web estática con datos simulados y una API serverless independiente. El código entregado incluye módulos de planificación, IA y seguimiento del riesgo. La integración del flujo completo entre interfaz, API y persistencia requiere validación adicional; no debe asumirse que todas las funciones propuestas estaban conectadas o desplegadas.

## Tecnologías del prototipo

Python, HTML, CSS, JavaScript, AWS Lambda, API Gateway, DynamoDB, Amazon Bedrock, S3, CloudFront y AWS SAM. La presencia de componentes o infraestructura en el proyecto no acredita por sí sola su funcionamiento actual.

## Estado de esta copia

Repositorio privado de preparación para portafolio. Incluye una copia del código y los documentos del ZIP de la entrega; se excluyeron cachés y archivos generados. Los identificadores de cuenta y enlaces del despliegue original se sustituyeron por ejemplos: es necesario configurar los recursos propios para desplegar. El equipo autorizó compartir el código públicamente. Esta copia requiere una revisión de seguridad antes de exponerse como servicio y la distribución detallada de las contribuciones del equipo está pendiente de precisar.

## Verificación de la copia

Se ejecutaron **91 pruebas automatizadas** de los directorios `src/` y `tests/` del ZIP entregado, con Python 3.12, pytest y boto3; todas pasaron. Estas pruebas usan datos y servicios simulados y no verifican un despliegue AWS ni un recorrido integrado de usuario. El código de esos directorios se copió al repositorio sin cambios de funcionalidad.

Una búsqueda automatizada de patrones habituales en los archivos actuales no encontró claves AWS, claves privadas ni tokens GitHub evidentes. Esto no equivale a una auditoría exhaustiva de seguridad ni demuestra que el prototipo sea apto para producción. Las direcciones de AWS e identificadores originales fueron sustituidos por valores de ejemplo; no se debe desplegar la configuración sin revisarla y ajustarla.

## EstudIA: evolución personal de Rumbo

EstudIA es una propuesta en desarrollo de Angela Soplin Costa, basada en Rumbo, creado en equipo por Los más Kiros para el Kiro IAThon. Esta iteración explora una identidad visual renovada, un perro peruano como tutor y un recorrido guiado de estudio. El nombre es una propuesta para esta versión; el proyecto original conserva su nombre y el reconocimiento al equipo.

## Iteración de UX: recorrido guiado

En `web/recorrido.html` se puede probar un primer recorrido de ejemplo con una mascota tutora: elegir objetivo, ver una ruta fija, responder una pregunta y celebrar el avance. Los contenidos son ficticios; no se cargan archivos, no se genera contenido con IA y el avance no se guarda. Para probarlo localmente, inicia un servidor estático en `web/` (por ejemplo, `python3 -m http.server 8000 --directory web`) y visita `/recorrido.html`.
