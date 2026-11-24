# Interfaz web

Esta carpeta contiene el prototipo visual de Rumbo, construido con HTML, CSS y JavaScript. Sus pantallas permiten explorar una experiencia de estudio con datos de demostración.

## Recorrido

1. `login.html`: acceso simulado con `demo / demo01`.
2. `onboarding.html`: configuración inicial de ejemplo.
3. `index.html` y `espacio.html?demo=1`: inicio y espacio de demostración.
4. `ruta.html` y `sesion.html`: ruta de aprendizaje y sesión guiada con contenido fijo.
5. `demo.html`: controles para simular una situación de atraso.

Inicia el servidor desde la raíz del repositorio con `python3 -m http.server 8000 --directory web` y abre `http://localhost:8000/login.html`.

La sesión se simula en el navegador. Las pantallas de carga y las funciones que requieren API necesitan configuración adicional y no están verificadas como un flujo integrado. Los nombres, documentos, citas y métricas de la demo son ficticios.
