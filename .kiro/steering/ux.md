---
inclusion: fileMatch
fileMatchPattern: ['src/pages/**', 'src/componentes/**', 'src/islas/**', 'src/layouts/**', 'src/estilos/**', '**/textos.ts', 'src/servidor/ia/prompts/**', '.kiro/specs/**']
---

# Experiencia de usuario y tono

## Tono de voz

Rumbo habla como un compañero que te conoce, no como un profesor ni una alarma.

| Hacer | Evitar |
|-------|--------|
| Tutear, frases cortas, español neutro con naturalidad peruana | Formalidad ("usted"), modismos muy locales |
| Hablar de lo que se puede hacer hoy | Recordar lo que faltó |
| Dar números concretos ("15 min", "faltan 6 días") | Frases vagas ("estudia más") |
| Celebrar el regreso | Contar los días perdidos |
| Ofrecer opciones | Dar órdenes |

Ejemplos:

- ✅ "Con 30 min hoy recuperas el ritmo para el jueves."
- ✅ "¿Día complicado? Una sesión de 5 minutos mantiene tu racha."
- ✅ "Reorganizamos tu ruta: Dinámica pasa al viernes."
- ❌ "Llevas 3 días sin estudiar." ❌ "Vas atrasado." ❌ "Perdiste tu racha."

Si la racha se reinicia: "Empiezas una racha nueva hoy" (nunca "perdiste").

## Navegación

Barra inferior en móvil y lateral en escritorio:

| Sección | Ruta | Contenido |
|---------|------|-----------|
| Hoy | `/` | Tarjeta "Tu sesión de hoy", ritmo, resumen diario, racha y XP |
| Espacios | `/espacios` | Lista de espacios y entrada a cada uno (documentos, temario, ruta, chat) |
| Calendario | `/calendario` | Vistas mensual y semanal |
| Progreso | `/progreso` | Vista general, síntesis semanal, insignias |
| Amigos | `/amigos` | Amigos, empujones, rutas compartidas, ligas |

El perfil se abre desde el avatar arriba a la derecha.

## Pantalla de inicio

En orden:

1. Saludo corto y ritmo ("🟢 Vas a buen ritmo").
2. **Tarjeta principal "Tu sesión de hoy"**: espacio, tema, duración estimada y un botón grande "Empezar" (o "Continuar" si está pausada). Si hay varios espacios, se muestra la sesión del examen más cercano y las demás debajo.
3. Si el riesgo es medio o mayor: tarjeta "Sesión de 5 minutos".
4. Resumen diario (colapsable, ~2 minutos de lectura).
5. Racha, comodín y XP de la semana.
6. Empujones recibidos.

Si el usuario no tiene espacios: un único botón "Crea tu primer espacio".

## Colores

Tokens en `@theme` de `src/estilos/global.css`:

| Token | Uso |
|-------|-----|
| `--color-marca` / `--color-marca-suave` | Botones principales, enlaces |
| `--color-dominado` (verde) | Tema dominado, sesión completada, riesgo bajo |
| `--color-progreso` (amarillo) | En progreso, riesgo medio |
| `--color-alerta` (naranja) | Riesgo alto |
| `--color-debil` (rojo suave) | Tema débil, riesgo crítico |
| `--color-no-visto` (gris) | No visto, bloqueado |
| `--color-espacio-1` … `--color-espacio-8` | Color de cada espacio en el calendario |

Los estados siempre llevan ícono o texto además del color.

## Componentes clave

- **Camino visual de la ruta:** nodos en zigzag vertical (estilo mapa de juego) con estados completado ✓, en curso ▶, disponible ○ y bloqueado 🔒. Muestra el nivel de la ruta y los días de simulacro y examen.
- **Sesión de estudio:** pantalla completa, un paso a la vez con barra de progreso: objetivo → material citado → práctica → flashcards → autoevaluación (1 a 5 caritas). Botones "Pausar" y "Preguntar al asistente" (abre el chat en un panel lateral sin salir).
- **Chat:** respuestas con chips de cita bajo cada párrafo y los botones rápidos de `ai-pipeline.md`.
- **Calendario:** sesiones como bloques de color del espacio, con ícono de estado. Arrastrar en escritorio; en móvil, mantener presionado y elegir el nuevo día.
- **Mapa conceptual:** nodos coloreados por dominio y flechas de prerrequisitos. Al tocar un nodo: resumen del tema y botón "Practicar este tema".
- **Celebraciones:** animación breve y no bloqueante para insignias, subida de nivel y ruta completada.

## Estados vacíos, carga y errores

- Cada lista vacía explica qué hacer: "Sube tus PDFs o diapositivas para empezar".
- Los procesos largos (procesar documentos, detectar temas) muestran pasos con progreso: "Leyendo tus documentos… 2 de 4".
- Los errores dicen qué pasó y qué hacer, sin códigos técnicos: "No pudimos leer este archivo. Prueba exportándolo a PDF".

## Rendimiento y conectividad

- Páginas SSR sin JavaScript donde se pueda. Presupuesto de JS por pantalla: < 150 KB comprimido (excepto calendario y mapa).
- Imágenes de avatares en SVG.
- El chat funciona con streaming para mostrar texto desde el primer segundo.
- Las acciones de práctica (responder, calificar flashcard) se envían en segundo plano y se reintentan si falla la red, para no bloquear la sesión en conexiones lentas.
