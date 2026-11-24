# Requisitos — Rumbo (producto)

Spec del producto que se construyó sobre el starter kit (`.kiro/specs/api-starter-kit/`). Parte de `contexto/rumbo-idea-principal.md`, `contexto/rumbo-funcionalidades.md` y del steering `product.md`. Cubre el flujo central de la historia de Lucía: subir PDFs, obtener temario y ruta, estudiar con la IA y recibir ayuda cuando aparece riesgo de abandono.

Todas las rutas son públicas (contrato de la Kiro IAthon). Solo se usan datos simulados.

## R1 — Crear un curso desde PDFs

**Historia:** como estudiante, quiero subir los PDFs de mi curso con la fecha del examen y mis minutos diarios, para que Rumbo arme mi plan.

1. CUANDO se hace `POST /cursos` con `{nombre, documentos:[{nombre, texto}], fechaExamen, minutosPorDia}`, ENTONCES la respuesta es `201` con el curso, sus temas y su ruta.
2. El texto de cada PDF se extrae en el navegador (pdf.js, hasta 30 páginas por archivo); la API recibe solo texto.
3. Se acepta el formato antiguo `{texto}` con un solo documento.
4. El curso guarda `creadoEn` con la fecha de Lima.

## R2 — Validación de entrada

**Historia:** como equipo, queremos rechazar entradas que rompan el guardado o disparen costos.

1. SI el cuerpo supera 1 MB, ENTONCES `413`.
2. SI un documento no termina en `.pdf`, ENTONCES `400` con un mensaje que lo nombra.
3. SI el curso tendría más de 10 documentos (contando los ya subidos), ENTONCES `400`.
4. SI un documento supera 120 000 caracteres o el curso supera 250 000, ENTONCES `413`.
5. SI el texto no es legible (menos del 85 % de caracteres imprimibles), ENTONCES `400` sugiriendo que puede ser un PDF escaneado.
6. SI `minutosPorDia` no es un entero entre 10 y 480, ENTONCES `400`.
7. SI `fechaExamen` no es `YYYY-MM-DD`, es hoy o anterior, o está a más de 365 días, ENTONCES `400`. Si viene vacía, se usa hoy + 10 días.
8. SI el curso serializado supera 380 KB (límite de ítem de DynamoDB: 400 KB), ENTONCES `413`.
9. El frontend aplica los mismos topes antes de enviar (10 PDFs, 20 MB por archivo).

## R3 — Temario con IA

**Historia:** como estudiante, quiero que los temas salgan de mis documentos.

1. La detección de temas usa Claude en Bedrock (Converse) y devuelve de 3 a 8 temas con `nombre`, `importancia` (1–3), `minutosEstimados` (15–90) y `requiere`.
2. La salida del modelo se valida: JSON extraído aunque venga con texto o cercas de código, campos acotados y prerrequisitos que apuntan solo a temas de la lista.
3. SI el modelo no responde, devuelve algo inválido o se agotó el cupo diario, ENTONCES se usa la heurística local (`temasFuente = "heuristica"`) y el flujo sigue.

## R4 — Ruta de estudio y modo rescate

1. La ruta reparte los temas en días desde hoy hasta el día anterior al examen sin pasar `minutosPorDia` por sesión.
2. Con 2 o más días, el último es un simulacro.
3. SI los minutos de los temas superan la capacidad, ENTONCES se activa el modo rescate: entran primero los temas de importancia 3, luego 2 y 1; el resto va a `temasFueraDePlan`.

## R5 — Gestionar documentos

1. `POST /cursos/{id}/documentos` agrega documentos (validados como en R2) y regenera temas y ruta.
2. `PUT /cursos/{id}/documentos` con `{incluidos:[ids]}` marca qué documentos entran en la ruta y la regenera. SI falta la lista, ENTONCES `400`.

## R6 — Chat sobre los documentos

1. `POST /cursos/{id}/chat` con `{pregunta}` responde usando solo los documentos incluidos.
2. SI la respuesta no está en los documentos, ENTONCES el modelo lo dice con la frase "No encontré esto en tus documentos".
3. El texto de los documentos va delimitado y el prompt indica ignorar instrucciones dentro de él.
4. SI la pregunta está vacía o supera 500 caracteres, ENTONCES `400` sin gastar cupo de IA.

## R7 — Plan de estudio redactado por IA

1. `POST /cursos/{id}/plan` redacta un párrafo de máximo 90 palabras, motivador y sin culpa, a partir del temario y la ruta.
2. Ante throttling se reintenta con espera exponencial (3 intentos); si persiste, se devuelve un plan de respaldo determinista (`fuente = "respaldo"`).
3. Errores no recuperables de Bedrock dan `502`.

## R8 — Registro de actividad

**Historia:** como estudiante, quiero marcar lo que estudié para que Rumbo sepa cómo voy.

1. `POST /cursos/{id}/actividad` acepta `evento` = `sesion_completada`, `sesion_abandonada`, `sesion_minima` o `respuestas`.
2. Los eventos de sesión se asocian a la primera sesión pendiente de `fechaSesion` (por defecto hoy) y cambian su `estado`.
3. `respuestas` exige `total` (1–200) y `aciertos` (0–`total`).
4. SI el evento no es válido o no hay sesión pendiente en esa fecha, ENTONCES `400`.
5. Registrar actividad recalcula el riesgo del día al momento.

## R9 — Alerta temprana de abandono

**Historia:** como estudiante que se atrasa, quiero que Rumbo lo note antes de que abandone y me proponga algo posible para hoy.

1. El riesgo es un puntaje de 0 a 100 con cinco factores ponderados (steering `algorithms.md`, sección 6): inactividad (30), atraso (25), caída de aciertos (15), sesiones a medias (15) y presión del examen (15).
2. Niveles: `bajo` 0–29, `medio` 30–54, `alto` 55–74, `critico` 75–100.
3. El usuario nunca ve el puntaje: ve su ritmo (🟢 "Vas a buen ritmo", 🟡 "Retoma con algo corto", 🟠 "Ajustamos tu plan", 🔴 "Hablemos de tu meta").
4. `GET /cursos/{id}/riesgo` calcula sin guardar. `POST /cursos/{id}/riesgo` calcula, guarda la evaluación y un historial de 30 días, y aplica la intervención.
5. Ambos aceptan `hoy` (hasta 60 días de la fecha real) para simular el paso de los días en la demo. Fuera de ese rango, `400`.
6. En la historia de demo (estudia el día 1 y pasa 3 días sin actividad), el nivel sube a `medio`.

## R10 — Intervenciones graduales y replanificación

1. `bajo`: recordatorio con los minutos de la sesión de hoy.
2. `medio`: propone la sesión mínima de 5 minutos.
3. `alto`: reorganiza la ruta y avisa que se prioriza lo esencial.
4. `critico`: ofrece ajustar disponibilidad, cambiar la fecha o ver el modo rescate.
5. CUANDO el nivel es `medio` o mayor y hay minutos atrasados, ENTONCES la ruta se replanifica: se conservan las sesiones completadas, los temas pendientes se reparten desde hoy sin acumular dos días en uno, `version` sube en 1 y se devuelve un aviso ("Reorganizamos tu ruta: X va el …").
6. Un mismo nivel (salvo `bajo`) no repite su intervención dos días seguidos.
7. Los mensajes no culpan: hablan de lo que se puede hacer hoy.

## R11 — Evaluación diaria programada

1. Una regla de EventBridge invoca la Lambda cada día a las 04:30 de Lima (09:30 UTC) con `{"tarea": "evaluar-riesgo"}`.
2. Se evalúa y guarda el riesgo de cada curso (hasta 1000). Un curso con datos incompletos no frena al resto.
3. Se registra en CloudWatch un resumen por nivel, sin datos personales.
4. `GET /cursos` incluye el `ritmo` de cada curso.

## R12 — Límites de uso de IA

**Historia:** como equipo, queremos que una API pública no genere costos inesperados en Bedrock.

1. Cupos diarios (hora de Lima): chat 40 por curso, plan 10 por curso, detección de temas 15 por curso, 80 llamadas por IP y 1500 globales. Se configuran por variables de entorno.
2. SI se agota un cupo en chat o plan, ENTONCES `429` con un mensaje sin culpa y sin llamar a Bedrock.
3. SI se agota en detección de temas, ENTONCES se usa la heurística (R3.3).
4. Los contadores son atómicos (escritura condicional de DynamoDB) y se borran solos con TTL.
5. API Gateway limita toda la API a 20 solicitudes por segundo (ráfaga de 40).
6. Los contadores no aparecen en `GET /items`.

## R13 — Interfaz

1. El espacio muestra "Tu ritmo" con el mensaje de la intervención, el aviso de ruta reorganizada y el botón "Completé mi sesión de hoy".
2. El panel de demo simula 3 días sin actividad llamando a `POST /cursos/{id}/riesgo` con una fecha adelantada.
3. Mobile-first, funciona a 360 px.

## R14 — Pruebas

1. `python -m pytest -q tests` cubre R1 a R12 sin tocar AWS (tabla y Bedrock falsos).
2. Las funciones de riesgo y replanificación se prueban como funciones puras con fechas fijas.
