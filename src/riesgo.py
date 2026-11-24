"""
Alerta temprana de abandono de Rumbo (ver .kiro/steering/algorithms.md, seccion 6).

Funciones puras y deterministas: reciben el curso y la fecha `hoy` por parametro,
no leen la BD ni la hora del sistema. El handler (app.py) guarda el resultado.

Flujo:
  1. `registrar_actividad` anota sesiones completadas/abandonadas y respuestas.
  2. `extraer_senales` resume la actividad en 5 senales numericas.
  3. `calcular_riesgo` pondera las senales -> puntaje 0-100 y nivel.
  4. `elegir_intervencion` decide la ayuda gradual segun el nivel (sin culpa).
  5. `evaluar` junta todo y, si el nivel es medio o mayor y hay atraso,
     pide replanificar la ruta (ruta.replanificar).
"""

from datetime import date, timedelta

# Pesos de cada factor (suman 100).
PESOS = {
    "inactividad": 30,
    "atraso": 25,
    "caida_aciertos": 15,
    "sesiones_a_medias": 15,
    "presion_examen": 15,
}

# Limite inferior de cada nivel, de mayor a menor.
UMBRALES = (
    (75, "critico"),
    (55, "alto"),
    (30, "medio"),
    (0, "bajo"),
)

DIAS_INACTIVIDAD_MAX = 4  # con 4 dias sin actividad el factor llega a 1
MIN_RESPUESTAS_VENTANA = 5  # respuestas minimas por ventana para medir caida
CAIDA_ACIERTOS_MAX = 0.3  # una caida de 30 puntos porcentuales es el maximo
RESPUESTAS_DIA_ACTIVO = 5  # glosario: dia activo = 5+ respuestas o sesion
DIAS_PRESION_ALTA = 7  # faltando 7 dias o menos la presion pesa completa
MAX_EVENTOS = 365  # historial de actividad guardado por curso
MAX_HISTORIAL_RIESGO = 30

EVENTOS_VALIDOS = ("sesion_completada", "sesion_abandonada", "sesion_minima", "respuestas")

# Lo que ve el usuario: nunca el puntaje, solo su ritmo.
RITMOS = {
    "bajo": {"emoji": "🟢", "texto": "Vas a buen ritmo"},
    "medio": {"emoji": "🟡", "texto": "Retoma con algo corto"},
    "alto": {"emoji": "🟠", "texto": "Ajustamos tu plan"},
    "critico": {"emoji": "🔴", "texto": "Hablemos de tu meta"},
}

ORDEN_NIVEL = {"bajo": 0, "medio": 1, "alto": 2, "critico": 3}


class ActividadInvalida(Exception):
    """La actividad enviada no es valida (el handler responde 400)."""


def _fecha(iso):
    return date.fromisoformat(iso)


def _entero(valor, nombre, minimo, maximo):
    if isinstance(valor, bool):
        raise ActividadInvalida(f"'{nombre}' debe ser un numero entero.")
    try:
        n = int(valor)
    except (TypeError, ValueError):
        raise ActividadInvalida(f"'{nombre}' debe ser un numero entero.")
    if not (minimo <= n <= maximo):
        raise ActividadInvalida(f"'{nombre}' debe estar entre {minimo} y {maximo}.")
    return n


# ---------------------------------------------------------------------------
# 1. Registro de actividad
# ---------------------------------------------------------------------------

def _buscar_sesion(sesiones, fecha_sesion, tipo):
    """Primera sesion de esa fecha que aun no esta completada."""
    for s in sesiones:
        if s.get("fecha") != fecha_sesion or s.get("estado") == "completada":
            continue
        if tipo and s.get("tipo") != tipo:
            continue
        return s
    return None


def registrar_actividad(curso, cuerpo, hoy):
    """Anota un evento de estudio en el curso. Modifica y devuelve el evento.

    cuerpo: {evento, fechaSesion?, tipo?, total?, aciertos?}
    """
    evento = cuerpo.get("evento")
    if evento not in EVENTOS_VALIDOS:
        raise ActividadInvalida("'evento' debe ser uno de: " + ", ".join(EVENTOS_VALIDOS) + ".")

    registro = {"fecha": hoy.isoformat(), "evento": evento}

    if evento in ("sesion_completada", "sesion_abandonada"):
        fecha_sesion = cuerpo.get("fechaSesion") or hoy.isoformat()
        try:
            _fecha(fecha_sesion)
        except (TypeError, ValueError):
            raise ActividadInvalida("'fechaSesion' debe tener formato YYYY-MM-DD.")
        sesion = _buscar_sesion(curso.get("ruta", {}).get("sesiones", []), fecha_sesion, cuerpo.get("tipo"))
        if sesion is None:
            raise ActividadInvalida("No hay una sesion pendiente en esa fecha.")
        if evento == "sesion_completada":
            sesion["estado"] = "completada"
            sesion["completadaEn"] = hoy.isoformat()
        else:
            sesion["estado"] = "abandonada"
        registro["fechaSesion"] = fecha_sesion

    if evento == "respuestas" or cuerpo.get("total") is not None:
        total = _entero(cuerpo.get("total"), "total", 1, 200)
        aciertos = _entero(cuerpo.get("aciertos", 0), "aciertos", 0, total)
        registro["total"] = total
        registro["aciertos"] = aciertos

    actividad = curso.setdefault("actividad", [])
    actividad.append(registro)
    del actividad[:-MAX_EVENTOS]
    return registro


# ---------------------------------------------------------------------------
# 2. Senales
# ---------------------------------------------------------------------------

def _dias_activos(actividad):
    """Fechas con sesion completada/minima o con 5+ respuestas."""
    respuestas_por_dia = {}
    activos = set()
    for e in actividad:
        if e["evento"] in ("sesion_completada", "sesion_minima"):
            activos.add(e["fecha"])
        if e.get("total"):
            respuestas_por_dia[e["fecha"]] = respuestas_por_dia.get(e["fecha"], 0) + e["total"]
    activos.update(f for f, n in respuestas_por_dia.items() if n >= RESPUESTAS_DIA_ACTIVO)
    return activos


def _tasa_aciertos(eventos):
    total = sum(e.get("total", 0) for e in eventos)
    if total < MIN_RESPUESTAS_VENTANA:
        return None
    return sum(e.get("aciertos", 0) for e in eventos) / total


def extraer_senales(curso, hoy):
    """Resume la actividad del curso en las senales del modelo de riesgo."""
    actividad = [e for e in curso.get("actividad", []) if _fecha(e["fecha"]) <= hoy]
    ruta = curso.get("ruta", {})
    sesiones = ruta.get("sesiones", [])
    minutos_por_dia = int(curso.get("minutosPorDia") or ruta.get("minutosPorDia") or 60)
    fecha_examen = _fecha(curso.get("fechaExamen") or ruta.get("fechaExamen"))

    # Inactividad: dias completos sin actividad desde el ultimo dia activo.
    # Crear el curso cuenta como punto de partida.
    activos = [_fecha(f) for f in _dias_activos(actividad)]
    inicio = curso.get("creadoEn") or (sesiones[0]["fecha"] if sesiones else hoy.isoformat())
    referencia = max(activos + [_fecha(inicio)])
    dias_sin_actividad = max(0, (hoy - referencia).days - 1) if referencia < hoy else 0

    estudio = [s for s in sesiones if s.get("tipo") == "estudio" and s.get("estado") != "completada"]
    minutos_atrasados = sum(s["minutos"] for s in estudio if _fecha(s["fecha"]) < hoy)
    limite_siguientes = hoy + timedelta(days=3)
    minutos_siguientes = sum(
        s["minutos"] for s in sesiones
        if s.get("estado") != "completada" and hoy <= _fecha(s["fecha"]) < limite_siguientes
    )

    inicio_reciente = hoy - timedelta(days=2)
    recientes = [e for e in actividad if e.get("total") and _fecha(e["fecha"]) >= inicio_reciente]
    previas = [e for e in actividad if e.get("total") and _fecha(e["fecha"]) < inicio_reciente]

    inicio_semana = hoy - timedelta(days=6)
    semana = [e for e in actividad if _fecha(e["fecha"]) >= inicio_semana]
    abandonadas = sum(1 for e in semana if e["evento"] == "sesion_abandonada")
    iniciadas = abandonadas + sum(1 for e in semana if e["evento"] == "sesion_completada")

    dias_al_examen = (fecha_examen - hoy).days
    return {
        "diasSinActividad": dias_sin_actividad,
        "minutosAtrasados": minutos_atrasados,
        "minutosSiguientes3Dias": minutos_siguientes,
        "aciertosPrevios": _tasa_aciertos(previas),
        "aciertosUltimos3Dias": _tasa_aciertos(recientes),
        "sesionesAbandonadas7Dias": abandonadas,
        "sesionesIniciadas7Dias": iniciadas,
        "minutosPendientes": sum(s["minutos"] for s in estudio),
        "capacidadRestante": max(0, dias_al_examen) * minutos_por_dia,
        "diasAlExamen": dias_al_examen,
    }


# ---------------------------------------------------------------------------
# 3. Puntaje y nivel
# ---------------------------------------------------------------------------

def _proporcion(parte, todo):
    """parte/todo acotado a 0..1. Si no hay base pero si hay parte, cuenta como 1."""
    if todo <= 0:
        return 1.0 if parte > 0 else 0.0
    return min(parte / todo, 1.0)


def calcular_riesgo(senales):
    """Devuelve {puntaje 0-100, nivel, factores[]} a partir de las senales."""
    s = senales
    caida = 0.0
    if s["aciertosPrevios"] is not None and s["aciertosUltimos3Dias"] is not None:
        caida = min(max(0.0, s["aciertosPrevios"] - s["aciertosUltimos3Dias"]) / CAIDA_ACIERTOS_MAX, 1.0)

    presion = _proporcion(s["minutosPendientes"], s["capacidadRestante"])
    presion *= 1.0 if s["diasAlExamen"] <= DIAS_PRESION_ALTA else 0.5

    valores = {
        "inactividad": min(s["diasSinActividad"] / DIAS_INACTIVIDAD_MAX, 1.0),
        "atraso": _proporcion(s["minutosAtrasados"], s["minutosSiguientes3Dias"]),
        "caida_aciertos": caida,
        "sesiones_a_medias": s["sesionesAbandonadas7Dias"] / max(1, s["sesionesIniciadas7Dias"]),
        "presion_examen": presion,
    }
    factores = [
        {"nombre": n, "valor": round(v, 3), "peso": PESOS[n], "aporte": round(v * PESOS[n], 1)}
        for n, v in valores.items()
    ]
    puntaje = int(round(sum(v * PESOS[n] for n, v in valores.items())))
    puntaje = max(0, min(100, puntaje))
    nivel = next(nombre for minimo, nombre in UMBRALES if puntaje >= minimo)
    return {"puntaje": puntaje, "nivel": nivel, "factores": factores}


# ---------------------------------------------------------------------------
# 4. Intervencion
# ---------------------------------------------------------------------------

def _minutos_de_hoy(curso, hoy):
    return sum(
        s["minutos"] for s in curso.get("ruta", {}).get("sesiones", [])
        if s.get("fecha") == hoy.isoformat() and s.get("estado") != "completada"
    )


def elegir_intervencion(nivel, curso, hoy, ultima=None):
    """Ayuda gradual segun el nivel. Mensajes sin culpa (product.md, principio 2).

    Un mismo nivel (salvo `bajo`) no repite su intervencion dos dias seguidos.
    """
    if ultima and nivel != "bajo" and ultima.get("nivel") == nivel:
        dias = (hoy - _fecha(ultima["fecha"])).days
        if 0 <= dias <= 1:
            return {"accion": "ninguna", "mensaje": RITMOS[nivel]["texto"] + ".", "repetida": True}

    if nivel == "bajo":
        minutos = _minutos_de_hoy(curso, hoy)
        mensaje = (
            f"Tu sesión de hoy te espera: {minutos} min." if minutos
            else "Hoy no tienes sesión. Si quieres, repasa unas flashcards."
        )
        return {"accion": "recordatorio", "mensaje": mensaje}
    if nivel == "medio":
        return {
            "accion": "sesion_minima",
            "mensaje": "¿Día complicado? Con una sesión de 5 minutos mantienes tu racha.",
            "minutos": 5,
        }
    if nivel == "alto":
        return {
            "accion": "ajustar_plan",
            "mensaje": "Reorganizamos tu ruta para que llegues a lo esencial antes del examen.",
        }
    return {
        "accion": "hablar_meta",
        "mensaje": "Vamos a ajustar tu meta para que sea alcanzable. Elige qué prefieres:",
        "opciones": ["ajustar_disponibilidad", "cambiar_fecha", "ver_modo_rescate"],
    }


# ---------------------------------------------------------------------------
# 5. Evaluacion completa
# ---------------------------------------------------------------------------

def evaluar(curso, hoy):
    """Calcula riesgo e intervencion. No modifica el curso.

    Devuelve {fecha, puntaje, nivel, ritmo, factores, senales, intervencion,
    debeReplanificar}.
    """
    senales = extraer_senales(curso, hoy)
    resultado = calcular_riesgo(senales)
    nivel = resultado["nivel"]
    ultima = curso.get("riesgo")
    intervencion = elegir_intervencion(nivel, curso, hoy, ultima)
    debe_replanificar = (
        ORDEN_NIVEL[nivel] >= ORDEN_NIVEL["medio"]
        and senales["minutosAtrasados"] > 0
        and not intervencion.get("repetida")
    )
    return {
        "fecha": hoy.isoformat(),
        "puntaje": resultado["puntaje"],
        "nivel": nivel,
        "ritmo": RITMOS[nivel],
        "factores": resultado["factores"],
        "senales": senales,
        "intervencion": intervencion,
        "debeReplanificar": debe_replanificar,
    }


def guardar_evaluacion(curso, evaluacion):
    """Guarda la ultima evaluacion y un historial corto en el curso."""
    curso["riesgo"] = {k: evaluacion[k] for k in ("fecha", "puntaje", "nivel", "ritmo", "intervencion")}
    historial = curso.setdefault("historialRiesgo", [])
    historial[:] = [h for h in historial if h["fecha"] != evaluacion["fecha"]]
    historial.append({"fecha": evaluacion["fecha"], "puntaje": evaluacion["puntaje"], "nivel": evaluacion["nivel"]})
    del historial[:-MAX_HISTORIAL_RIESGO]
