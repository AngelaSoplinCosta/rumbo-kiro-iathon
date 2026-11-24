"""
Generador de temario y ruta de aprendizaje a partir del texto de un PDF.

Heuristica determinista (sin dependencias externas): detecta temas desde los
titulos/lineas del documento, estima minutos por tema segun el volumen de texto
y reparte los temas en dias hasta la fecha del examen respetando los minutos
disponibles por dia.

La deteccion principal usa Bedrock (`ia.detectar_temas_ia`); esta heuristica es
el respaldo cuando el modelo no responde o se agoto el limite diario de IA.
"""

import re
from datetime import date, timedelta

# Palabras que suelen encabezar temas en material academico.
_PISTAS_TITULO = (
    "capitulo", "capítulo", "unidad", "tema", "leccion", "lección",
    "introduccion", "introducción", "parte", "seccion", "sección",
)

# Temas "esenciales" por palabras clave frecuentes (importancia 3).
_ESENCIALES = ("ley", "teorema", "principio", "ecuacion", "ecuación", "fundamento")


def _limpiar(texto):
    return re.sub(r"\s+", " ", (texto or "")).strip()


def _parece_titulo(linea):
    l = linea.strip()
    if not (3 <= len(l) <= 80):
        return False
    bajo = l.lower()
    if any(bajo.startswith(p) or (" " + p) in bajo[:20] for p in _PISTAS_TITULO):
        return True
    # Numeracion tipo "1." "2.3" "Capitulo 1"
    if re.match(r"^\d+(\.\d+)*[\).\-\s]", l):
        return True
    # Linea corta en mayusculas (titulo en mayusculas)
    if l.isupper() and len(l.split()) <= 8:
        return True
    return False


def detectar_temas(texto, maximo=8):
    """Devuelve una lista de temas detectados desde el texto del PDF."""
    texto = texto or ""
    lineas = [l for l in texto.splitlines() if l.strip()]

    titulos = []
    vistos = set()
    for linea in lineas:
        if _parece_titulo(linea):
            nombre = _limpiar(re.sub(r"^\d+(\.\d+)*[\).\-\s]+", "", linea)).title()
            clave = nombre.lower()
            if nombre and clave not in vistos and len(nombre) > 2:
                vistos.add(clave)
                titulos.append(nombre)

    # Si el PDF no tiene titulos claros, partimos el texto en bloques.
    if len(titulos) < 3:
        palabras = _limpiar(texto).split()
        bloques = max(3, min(maximo, len(palabras) // 180 or 3))
        tam = max(1, len(palabras) // bloques)
        titulos = []
        for i in range(bloques):
            trozo = palabras[i * tam : (i + 1) * tam]
            if not trozo:
                break
            titulos.append("Tema " + str(i + 1) + ": " + " ".join(trozo[:4]).title())

    titulos = titulos[:maximo]

    temas = []
    for i, nombre in enumerate(titulos):
        bajo = nombre.lower()
        importancia = 3 if any(k in bajo for k in _ESENCIALES) else (2 if i < len(titulos) - 1 else 1)
        # Minutos estimados: base 30, +15 si es esencial, acotado 20..60.
        minutos = 30 + (15 if importancia == 3 else 0)
        minutos = max(20, min(60, minutos))
        temas.append(
            {
                "orden": i + 1,
                "nombre": nombre[:80],
                "importancia": importancia,
                "minutosEstimados": minutos,
                # El tema anterior es prerrequisito del siguiente (cadena simple).
                "requiere": ([titulos[i - 1][:80]] if i > 0 else []),
            }
        )
    return temas


def _dias_disponibles(hoy, fecha_examen, minutos_por_dia):
    """Fechas desde hoy hasta el dia anterior al examen (una sesion por dia)."""
    dias = []
    d = hoy
    while d < fecha_examen:
        dias.append(d)
        d += timedelta(days=1)
    return dias


def generar_ruta(temas, hoy, fecha_examen, minutos_por_dia=60):
    """Reparte los temas en dias. Activa modo rescate si el tiempo no alcanza."""
    dias = _dias_disponibles(hoy, fecha_examen, minutos_por_dia)
    total_min_temas = sum(t["minutosEstimados"] for t in temas)
    capacidad = len(dias) * minutos_por_dia

    modo_rescate = total_min_temas > capacidad and len(dias) > 0
    planificables = list(temas)
    temas_fuera = []
    if modo_rescate:
        # Prioriza importancia 3, luego 2, luego 1, hasta llenar la capacidad.
        ordenados = sorted(temas, key=lambda t: (-t["importancia"], t["orden"]))
        acumulado = 0
        esenciales = []
        for t in ordenados:
            if acumulado + t["minutosEstimados"] <= capacidad:
                esenciales.append(t)
                acumulado += t["minutosEstimados"]
            else:
                temas_fuera.append(t["nombre"])
        planificables = sorted(esenciales, key=lambda t: t["orden"])

    sesiones = []
    if not dias:
        # Examen manana o sin dias: una sola sesion hoy con lo esencial.
        sesiones.append(
            {
                "fecha": hoy.isoformat(),
                "tipo": "estudio",
                "temas": [t["nombre"] for t in planificables],
                "minutos": min(minutos_por_dia, total_min_temas),
            }
        )
        modo_rescate = True
    else:
        i_dia = 0
        min_dia = 0
        actual = {"fecha": dias[0].isoformat(), "tipo": "estudio", "temas": [], "minutos": 0}
        for t in planificables:
            if min_dia + t["minutosEstimados"] > minutos_por_dia and actual["temas"]:
                sesiones.append(actual)
                i_dia += 1
                if i_dia >= len(dias):
                    i_dia = len(dias) - 1  # ultimo dia acumula el resto
                min_dia = 0
                actual = {"fecha": dias[i_dia].isoformat(), "tipo": "estudio", "temas": [], "minutos": 0}
            actual["temas"].append(t["nombre"])
            actual["minutos"] += t["minutosEstimados"]
            min_dia += t["minutosEstimados"]
        if actual["temas"]:
            sesiones.append(actual)
        # Ultimo dia disponible: simulacro.
        if len(dias) >= 2:
            sesiones.append(
                {"fecha": dias[-1].isoformat(), "tipo": "simulacro", "temas": ["Simulacro final"], "minutos": minutos_por_dia}
            )

    return {
        "dias": len(dias),
        "minutosPorDia": minutos_por_dia,
        "modoRescate": modo_rescate,
        "temasFueraDePlan": temas_fuera,
        "sesiones": sesiones,
        "fechaExamen": fecha_examen.isoformat(),
    }


def replanificar(curso, hoy):
    """Recalcula la ruta desde `hoy` con los temas que siguen pendientes.

    Reglas (algorithms.md, seccion 2): las sesiones completadas se conservan; las
    pasadas sin completar se descartan y sus temas vuelven a pendientes, que se
    reparten en los dias que quedan (nunca se acumulan dos dias en uno). Si el
    tiempo no alcanza, `generar_ruta` activa el modo rescate.
    Modifica el curso y devuelve un aviso corto para el usuario.
    """
    ruta_actual = curso.get("ruta", {})
    sesiones = ruta_actual.get("sesiones", [])
    completadas = [s for s in sesiones if s.get("estado") == "completada"]
    temas_hechos = {t for s in completadas for t in s.get("temas", [])}
    pendientes = [t for t in curso.get("temas", []) if t["nombre"] not in temas_hechos]

    fecha_examen = date.fromisoformat(curso["fechaExamen"])
    minutos = int(curso.get("minutosPorDia") or 60)
    nueva = generar_ruta(pendientes, hoy, fecha_examen, minutos)
    nueva["sesiones"] = completadas + nueva["sesiones"]
    nueva["version"] = int(ruta_actual.get("version", 1)) + 1
    curso["ruta"] = nueva

    proxima = next(
        (s for s in nueva["sesiones"] if s.get("estado") != "completada" and s["tipo"] == "estudio"),
        None,
    )
    if proxima is None:
        return "Reorganizamos tu ruta: ya cubriste todos los temas, quedan los repasos."
    aviso = f"Reorganizamos tu ruta: {proxima['temas'][0]} va el {proxima['fecha']}."
    if nueva["modoRescate"]:
        aviso += " Nos enfocamos en lo esencial para llegar al examen."
    return aviso


def _fecha_valida(fecha_examen_iso, hoy):
    try:
        f = date.fromisoformat(fecha_examen_iso)
    except (TypeError, ValueError):
        f = hoy + timedelta(days=10)
    if f <= hoy:
        f = hoy + timedelta(days=10)
    return f


def _detectar_temas_con_ia(texto):
    """Usa Bedrock para detectar temas; si falla, cae a la heuristica local.

    Se importa `ia` de forma diferida para no acoplar los tests de `ruta` a Bedrock.
    """
    try:
        import ia as _ia

        temas = _ia.detectar_temas_ia(texto)
        if temas:
            return temas, "bedrock"
    except Exception:
        pass
    return detectar_temas(texto), "heuristica"


def regenerar(curso, hoy=None, detector=None, usar_ia=True):
    """Recalcula temas y ruta con los documentos marcados como incluidos.

    `curso` debe tener: nombre, fechaExamen, minutosPorDia y documentos[].
    Solo los documentos con `incluir` != False entran en la ruta.
    `detector` permite inyectar la deteccion de temas en pruebas; por defecto usa
    Bedrock con respaldo a la heuristica local. Con `usar_ia=False` (limite diario
    de IA agotado) se usa directamente la heuristica.
    Devuelve el mismo dict con `temas`, `ruta`, `temasFuente` y `caracteresTexto`.
    """
    hoy = hoy or date.today()
    documentos = curso.get("documentos", [])
    incluidos = [d for d in documentos if d.get("incluir", True)]
    # Si el usuario desmarco todo, se usan todos para no dejar la ruta vacia.
    if not incluidos:
        incluidos = documentos
    texto = "\n".join(d.get("texto", "") for d in incluidos)

    fecha_examen = _fecha_valida(curso.get("fechaExamen"), hoy)
    minutos = int(curso.get("minutosPorDia") or 60)

    if detector is not None:
        temas, fuente = detector(texto), "inyectado"
    elif usar_ia:
        temas, fuente = _detectar_temas_con_ia(texto)
    else:
        temas, fuente = detectar_temas(texto), "heuristica"
    ruta = generar_ruta(temas, hoy, fecha_examen, minutos)

    curso["temas"] = temas
    curso["temasFuente"] = fuente
    curso["ruta"] = ruta
    curso["caracteresTexto"] = len(texto)
    curso["fechaExamen"] = fecha_examen.isoformat()
    return curso


def nuevo_documento(nombre_archivo, texto):
    """Crea el dict de un documento del espacio."""
    import uuid as _uuid

    return {
        "id": _uuid.uuid4().hex,
        "nombre": nombre_archivo or "documento.pdf",
        "texto": texto or "",
        "caracteres": len(texto or ""),
        "incluir": True,
    }


def construir_curso(nombre, documentos, fecha_examen_iso, minutos_por_dia=60, hoy=None, detector=None, usar_ia=True):
    """Crea un curso nuevo con una lista de documentos y genera su ruta.

    `documentos` es una lista de {nombre, texto}.
    """
    hoy = hoy or date.today()
    docs = [nuevo_documento(d.get("nombre"), d.get("texto")) for d in (documentos or [])]
    curso = {
        "nombre": nombre or "Curso sin nombre",
        "fechaExamen": fecha_examen_iso,
        "minutosPorDia": int(minutos_por_dia or 60),
        "documentos": docs,
        "creadoEn": hoy.isoformat(),
    }
    return regenerar(curso, hoy, detector=detector, usar_ia=usar_ia)


