---
inclusion: fileMatch
fileMatchPattern: ['src/servidor/dominio/**', 'src/servidor/modulos/rutas/**', 'src/servidor/modulos/sesiones/**', 'src/servidor/modulos/practica/**', 'src/servidor/modulos/riesgo/**', 'src/servidor/modulos/gamificacion/**', 'src/servidor/modulos/ranking/**', '.kiro/specs/**']
---

# Algoritmos del dominio

Todo vive en `src/servidor/dominio/` como funciones puras, con pruebas en Vitest. Reciben `hoy: FechaISO` por parámetro. Los valores numéricos de este documento son constantes iniciales, definidas en `dominio/constantes.ts` para poder ajustarlas.

## 1. Planificador de la ruta

`planificarRuta(entrada): PlanRuta`

### Entrada

- `hoy`, `fechaExamen`.
- `disponibilidad`: minutos por día de la semana.
- `temas`: unidades planificables (subtemas o temas sin hijos) con `minutosEstimados`, `importancia`, `orden`, prerrequisitos y `dominio` (0–1).
- `sesionesFijadas`: sesiones movidas a mano que se respetan.
- `temasPrioritarios`: del plan de refuerzo semanal (opcional).

### Pasos

1. **Días disponibles:** fechas desde `hoy` hasta el día anterior al examen con `minutos > 0`. El día del examen no se planifica.
2. **Temas pendientes:** se excluyen los temas con dominio ≥ 0.8 (dominados en el diagnóstico o ya completados).
3. **Orden:** ordenamiento topológico (Kahn) usando como desempate: primero `temasPrioritarios`, luego `orden`.
4. **Reserva de días especiales** (contados desde el final):
   - Simulacros: el último día disponible si hay ≥ 4 días; los 2 últimos si hay ≥ 10.
   - Margen: 1 día por cada 7 días disponibles (redondeo hacia abajo), mínimo 1 si hay ≥ 5 días. Se ubica justo antes de los simulacros y, si hay más de uno, repartido uniformemente.
5. **Capacidad de estudio:** suma de minutos de los días restantes × 0.8. El 20 % de cada día se reserva para repaso (flashcards vencidas y preguntas de temas anteriores).
6. **Modo rescate:** si `suma(minutosEstimados pendientes) > capacidad` se activa (ver punto 3).
7. **Asignación (llenado voraz):** se recorren los temas en orden y se asignan a los días en orden:
   - Un tema puede dividirse entre días consecutivos si no entra (partes de mínimo 15 minutos).
   - Un tema no empieza el mismo día que su prerrequisito termina, salvo que el prerrequisito termine en la primera mitad del día.
   - Una sesión por día y espacio, que puede tener varios temas.
8. **Días de repaso:** cada 4 días de estudio se inserta un día de tipo `repaso` si quedan días libres después de la asignación; si no hay días libres, se mantiene solo el 20 % diario.
9. **Salida:** lista de `{ fecha, tipo, temas[{ temaId, minutos, parte, totalPartes }], minutosEstimados }`, `esModoRescate`, `temasFueraDePlan`, `minutosSobrantes`.

Si no hay ningún día disponible (examen mañana o sin disponibilidad), se devuelve un plan de una sola sesión hoy con los temas esenciales y `esModoRescate = true`.

## 2. Replanificación

`replanificarRuta(rutaActual, progreso, hoy)` usa el mismo planificador con lo pendiente.

**Cuándo se ejecuta:**

- En `cierre-del-dia`, si alguna sesión de estudio de ayer quedó sin completar (atraso) o si el usuario completó temas de días futuros (adelanto).
- Cuando el usuario cambia la fecha del examen, su disponibilidad o el temario.
- Cuando el nivel de riesgo es medio o mayor (ver punto 5).
- Cuando hay un plan de refuerzo nuevo (domingo).

**Reglas:**

- Las sesiones pasadas no completadas pasan a `vencida`; sus temas vuelven a pendientes. **Nunca se acumulan dos días de trabajo en uno**: se reparten en los días que quedan.
- Primero se consumen los días de margen.
- Las sesiones fijadas se respetan y sus minutos se descuentan de su día.
- La versión de la ruta sube en 1. El usuario ve un aviso: "Reorganizamos tu ruta: el tema X pasa al jueves".

## 3. Modo rescate

Cuando la capacidad no alcanza:

1. Se marca como obligatorio todo tema con importancia 3 y, recursivamente, sus prerrequisitos pendientes.
2. Si lo obligatorio entra: se agregan temas de importancia 2 en orden topológico hasta llenar la capacidad, y luego de importancia 1.
3. Si lo obligatorio no entra: se reducen los minutos de cada tema obligatorio de forma proporcional hasta un mínimo del 60 %; si aún no entra, se descartan los esenciales con menos prerrequisitos dependientes, empezando por los últimos en el orden.
4. Se eliminan los días de repaso y de margen, y se deja un solo simulacro.
5. Los temas excluidos se guardan en `temas_fuera_de_plan` y se muestran como "Si te sobra tiempo".

El modo rescate se desactiva solo si una replanificación posterior vuelve a tener capacidad suficiente.

## 4. Repetición espaciada (SM-2)

`calificarFlashcard(estado, calificacion, hoy)` con la variante estándar de SM-2. La UI ofrece 4 botones que se mapean a calificaciones:

| Botón | Calificación |
|-------|--------------|
| Otra vez | 1 |
| Difícil | 3 |
| Bien | 4 |
| Fácil | 5 |

- Si `calificacion < 3`: `repeticiones = 0`, `intervalo = 1`.
- Si no: `repeticiones` 1 → intervalo 1; 2 → 6; después `round(intervalo × facilidad)`.
- `facilidad = max(1.3, facilidad + 0.1 − (5 − q) × (0.08 + (5 − q) × 0.02))`.
- `proxima_revision = hoy + intervalo`, sin pasar del día anterior al examen (las tarjetas se comprimen antes del examen).
- "Otra vez" vuelve a mostrar la tarjeta al final de la sesión actual.

Las flashcards nuevas de un tema entran al terminar la sesión de estudio de ese tema.

## 5. Dominio por tema

`calcularDominio(respuestas, repasos)`:

- Puntaje = promedio ponderado de las respuestas del tema, con peso `0.85^k` (k = posición desde la más reciente), mezclado 70 % preguntas y 30 % flashcards (calificación ≥ 4 cuenta como acierto).
- Estado:
  - `no_visto`: sin respuestas.
  - `debil`: puntaje < 0.5 con al menos 3 respuestas.
  - `en_progreso`: el resto.
  - `dominado`: puntaje ≥ 0.8 con al menos 5 respuestas (o diagnóstico correcto en el tema).
- Diagnóstico: una respuesta correcta en un tema principal marca sus subtemas con `puntaje = 0.8` y `es_por_diagnostico = true`. Las respuestas posteriores reemplazan este valor.

## 6. Riesgo de abandono

`calcularRiesgo(señales, hoy)` devuelve `{ puntaje 0–100, nivel, factores }`. Se calcula por ruta activa cada mañana.

| Factor | Cálculo (0–1) | Peso |
|--------|---------------|------|
| Inactividad | `min(diasSinActividad / 4, 1)` | 30 |
| Atraso | `min(minutosAtrasados / minutosDeLos3DiasSiguientes, 1)` | 25 |
| Caída de aciertos | `max(0, aciertosPrevios − aciertosUltimos3Dias) / 0.3`, con tope 1. Solo si hay ≥ 5 respuestas en cada ventana. | 15 |
| Sesiones a medias | `abandonadasUltimos7Dias / max(1, iniciadasUltimos7Dias)` | 15 |
| Presión del examen | `pendiente / capacidadRestante`, con tope 1, multiplicado por 1 si faltan ≤ 7 días y por 0.5 en otro caso | 15 |

`puntaje = round(Σ factor × peso)`.

| Nivel | Puntaje | Intervención |
|-------|---------|--------------|
| `bajo` | 0–29 | Recordatorio normal a la hora preferida. |
| `medio` | 30–54 | Propone la sesión mínima de 5 min en la pantalla de inicio y en la notificación, y replanifica. |
| `alto` | 55–74 | Replanifica activando el modo rescate si hace falta. Si `permitir_aviso_a_amigos_en_riesgo`, notifica a sus amigos aceptados que siguen la misma ruta original ("A Lucía le vendría bien un empujón"). |
| `critico` | 75–100 | Mensaje empático con tres opciones: ajustar disponibilidad, cambiar la fecha o meta, o ver la ruta en modo rescate. |

Reglas:

- Un mismo nivel no repite su intervención dos días seguidos, salvo el recordatorio.
- Si el usuario completa una sesión, el riesgo del día se recalcula al momento.
- El usuario nunca ve el puntaje. Ve su **ritmo**: 🟢 "Vas a buen ritmo", 🟡 "Retoma con algo corto", 🟠 "Ajustamos tu plan", 🔴 "Hablemos de tu meta".

## 7. Racha y comodines

- Un día cuenta para la racha si el usuario completó al menos una sesión (normal o mínima) ese día.
- En `cierre-del-dia` (para el día de ayer):
  - Si ayer contó: `racha_actual += 1`.
  - Si no contó y `comodines_disponibles = 1`: se usa el comodín (`uso_comodin`), la racha se mantiene y se notifica "Usamos tu comodín de la semana".
  - Si no contó y no hay comodín: `racha_actual = 0`.
- Los lunes `comodines_disponibles = 1` (no se acumulan).

## 8. XP y niveles

| Acción | XP |
|--------|----|
| Respuesta correcta | 10 |
| Respuesta incorrecta | 2 |
| Flashcard repasada | 3 |
| Sesión completada | 50 |
| Sesión mínima completada | 20 |
| Simulacro completado | 100 |
| Ruta completada antes del examen | 300 |

- Límite: 150 XP por respuestas y flashcards por día y ruta, para evitar farmear.
- Nivel por ruta: `nivel = floor(sqrt(xpRuta / 100)) + 1`. XP para el nivel n: `100 × (n − 1)²`.

## 9. Insignias

| Clave | Condición |
|-------|-----------|
| `primer_tema_dominado` | Primer `dominio_tema.estado = dominado` (no por diagnóstico). |
| `racha_7` | `racha_actual` llega a 7. |
| `primer_simulacro` | Primera sesión de tipo `simulacro` completada. |
| `volvi` | Completa una sesión después de 3 o más días sin días activos. |
| `ruta_completada` | Todas las sesiones de estudio completadas antes de la fecha del examen. Otorga además la recompensa final (pantalla de celebración y 300 XP). |

Se evalúan al recibir los eventos `sesion.completada`, `dominio.actualizado` y `racha.actualizada`.

## 10. Ligas y ranking

- Las ligas agrupan rutas con la misma `ruta_origen_id` (la original también participa).
- Cada lunes a las 00:05 se cierra la semana: se guarda `posicion_final` y se crean ligas nuevas.
- Armado: los participantes (no ocultos) se ordenan por fecha de ingreso y se reparten en ligas de máximo 30. Si quedan menos de 10 en la última, se unen a la anterior. Si hay menos de 10 en total, se forma una sola liga igual (en el hackathon habrá pocas personas).
- Quien copia una ruta a mitad de semana entra a la liga con espacio de la semana en curso.
- **Puntaje de avance:** `minutosCompletadosEnLaSemana / minutosTotalesDeLaRuta` (solo cuenta práctica dentro de sesiones con al menos 1 respuesta).
- **Puntaje de constancia:** días activos de la semana (≥ 5 respuestas o flashcards en el día).
- Empates: gana quien tiene más `preguntas_respondidas`.
- El tiempo con la app abierta nunca suma puntaje.
