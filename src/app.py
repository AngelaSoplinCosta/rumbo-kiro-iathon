"""
API del starter kit de Rumbo para la Kiro IAthon.

Rutas publicas (sin autenticacion):
  GET  /health        -> contrato de la insignia "API viva".
  POST /items         -> crea un item (insignia "Persistencia").
  GET  /items/{id}    -> obtiene un item por id.
  GET  /items         -> lista hasta 100 items (paginando el scan).
  POST /cursos                  -> recibe el texto de los PDFs y genera temario + ruta.
  GET  /cursos                  -> lista los cursos con su ritmo.
  GET  /cursos/{id}             -> devuelve un curso con su ruta.
  POST /cursos/{id}/documentos  -> agrega documentos y regenera la ruta.
  PUT  /cursos/{id}/documentos  -> elige que documentos entran en la ruta.
  POST /cursos/{id}/chat        -> IA: responde solo con los documentos del curso.
  POST /cursos/{id}/plan        -> IA: redacta el plan de estudio.
  POST /cursos/{id}/actividad   -> registra sesiones y respuestas del estudiante.
  GET  /cursos/{id}/riesgo      -> calcula el riesgo de abandono (sin guardar).
  POST /cursos/{id}/riesgo      -> calcula, guarda y aplica la intervencion.
  Evento programado (EventBridge, diario) -> evalua el riesgo de todos los cursos.

El handler es un router minimo para API Gateway (payload HTTP API v2 y REST v1).
No usa frameworks externos: solo boto3, que ya viene en el runtime de Lambda.
"""

import json
import os
import uuid
from datetime import date, timedelta

import boto3
from botocore.exceptions import ClientError

import ia as ia_mod
import limites
import riesgo as riesgo_mod
import ruta as ruta_mod
import validacion

# Nombre de la tabla DynamoDB. Llega como variable de entorno desde template.yaml.
# Se lee de forma diferida (dentro de las funciones) para que los tests puedan
# hacer monkeypatch de TABLE con una tabla falsa.
TABLE_NAME = os.environ.get("TABLE_NAME", "")

# Id publico del equipo. Llega como variable de entorno TEAM_ID desde template.yaml.
TEAM_ID = os.environ.get("TEAM_ID", "")

# Referencia a la tabla. Los tests la reemplazan con un doble (monkeypatch de TABLE).
TABLE = None


def _tabla():
    """Devuelve la tabla DynamoDB, creandola la primera vez (lazy)."""
    global TABLE
    if TABLE is None:
        TABLE = boto3.resource("dynamodb").Table(TABLE_NAME)
    return TABLE


def _respuesta(codigo, cuerpo):
    """Arma una respuesta de API Gateway con JSON y content-type correcto."""
    return {
        "statusCode": codigo,
        "headers": {
            "content-type": "application/json",
            "access-control-allow-origin": "*",
        },
        "body": json.dumps(cuerpo),
    }


def _metodo_y_ruta(event):
    """Extrae metodo y ruta tanto del payload HTTP API v2 como del REST v1."""
    ctx = event.get("requestContext", {})
    if "http" in ctx:  # HTTP API (payload v2)
        metodo = ctx["http"]["method"]
        ruta = ctx["http"].get("path") or event.get("rawPath", "")
    else:  # REST API (payload v1)
        metodo = event.get("httpMethod", "")
        ruta = event.get("path", "")
    # Normaliza: sin barra final (salvo la raiz).
    if len(ruta) > 1 and ruta.endswith("/"):
        ruta = ruta.rstrip("/")
    return metodo, ruta


def _id_de_ruta(event, ruta):
    """Obtiene el {id} de /items/{id} desde pathParameters o desde la ruta."""
    params = event.get("pathParameters") or {}
    if params.get("id"):
        return params["id"]
    partes = ruta.split("/")
    if len(partes) >= 3 and partes[1] == "items":
        return partes[2]
    return None


def _crear_item(event):
    try:
        cuerpo = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _respuesta(400, {"error": "cuerpo JSON invalido"})

    valor = cuerpo.get("value")
    if valor is None:
        return _respuesta(400, {"error": "falta el campo 'value'"})

    nuevo_id = uuid.uuid4().hex
    item = {"id": nuevo_id, "value": valor}
    _tabla().put_item(Item=item)
    return _respuesta(201, item)


def _obtener_item(item_id):
    resultado = _tabla().get_item(Key={"id": item_id})
    item = resultado.get("Item")
    if not item:
        return _respuesta(404, {"error": "no encontrado"})
    return _respuesta(200, {"id": item["id"], "value": item.get("value")})


def _listar_items():
    """Lista hasta 100 items paginando el scan (nunca solo la primera pagina)."""
    items = []
    clave_siguiente = None
    while len(items) < 100:
        kwargs = {"Limit": 100}
        if clave_siguiente:
            kwargs["ExclusiveStartKey"] = clave_siguiente
        resultado = _tabla().scan(**kwargs)
        # Los contadores de limites de IA son internos: no se listan.
        items.extend(i for i in resultado.get("Items", []) if i.get("tipo") != "limite")
        clave_siguiente = resultado.get("LastEvaluatedKey")
        if not clave_siguiente:
            break
    items = items[:100]
    limpios = [{"id": i.get("id"), "value": i.get("value")} for i in items]
    return _respuesta(200, {"items": limpios})


def _ip(event):
    """IP de origen del cliente (para el cupo diario de IA por IP)."""
    ctx = event.get("requestContext", {})
    return (ctx.get("http") or {}).get("sourceIp") or (ctx.get("identity") or {}).get("sourceIp")


def _error_entrada(e):
    return _respuesta(e.codigo, {"error": str(e)})


def _puede_usar_ia(operacion, curso_id, event):
    """Reserva cupo para una llamada a Bedrock. False si se agoto el limite diario."""
    try:
        limites.consumir(_tabla(), operacion, curso_id=curso_id, ip=_ip(event))
        return True
    except limites.LimiteExcedido:
        print("LIMITE_IA", operacion, curso_id)
        return False


def _guardar_curso(curso_id, curso):
    _tabla().put_item(Item={"id": curso_id, "tipo": "curso", "value": json.dumps(curso)})


def _leer_curso(curso_id):
    resultado = _tabla().get_item(Key={"id": curso_id})
    item = resultado.get("Item")
    if not item or item.get("tipo") != "curso":
        return None
    return json.loads(item["value"])


def _crear_curso(event):
    """Crea un espacio con uno o varios documentos y genera la ruta."""
    hoy = limites.hoy_lima()
    try:
        cuerpo = validacion.leer_cuerpo(event)
        datos = validacion.validar_curso(cuerpo, hoy)
        documentos = validacion.validar_documentos(cuerpo)
    except validacion.EntradaInvalida as e:
        return _error_entrada(e)

    curso = ruta_mod.construir_curso(
        nombre=datos["nombre"],
        documentos=documentos,
        fecha_examen_iso=datos["fechaExamen"],
        minutos_por_dia=datos["minutosPorDia"],
        hoy=hoy,
        usar_ia=_puede_usar_ia("temas", None, event),
    )
    try:
        validacion.validar_tamano_curso(curso)
    except validacion.EntradaInvalida as e:
        return _error_entrada(e)
    curso_id = uuid.uuid4().hex
    _guardar_curso(curso_id, curso)
    curso["id"] = curso_id
    return _respuesta(201, curso)


def _agregar_documentos(event, curso_id):
    """Suma documentos a un espacio existente y regenera la ruta."""
    curso = _leer_curso(curso_id)
    if curso is None:
        return _respuesta(404, {"error": "curso no encontrado"})

    existentes = curso.get("documentos", [])
    try:
        cuerpo = validacion.leer_cuerpo(event)
        nuevos = validacion.validar_documentos(
            cuerpo,
            ya_subidos=len(existentes),
            texto_existente=sum(len(d.get("texto", "")) for d in existentes),
        )
    except validacion.EntradaInvalida as e:
        return _error_entrada(e)

    for d in nuevos:
        curso.setdefault("documentos", []).append(
            ruta_mod.nuevo_documento(d.get("nombre"), d.get("texto"))
        )
    # Recalcula temas y ruta con todos los documentos.
    ruta_mod.regenerar(curso, limites.hoy_lima(), usar_ia=_puede_usar_ia("temas", curso_id, event))
    try:
        validacion.validar_tamano_curso(curso)
    except validacion.EntradaInvalida as e:
        return _error_entrada(e)
    _guardar_curso(curso_id, curso)
    curso["id"] = curso_id
    return _respuesta(200, curso)


def _obtener_curso(curso_id):
    curso = _leer_curso(curso_id)
    if curso is None:
        return _respuesta(404, {"error": "curso no encontrado"})
    curso["id"] = curso_id
    return _respuesta(200, curso)


def _chat_curso(event, curso_id):
    """Chat con IA sobre los documentos del curso (solo los incluidos)."""
    curso = _leer_curso(curso_id)
    if curso is None:
        return _respuesta(404, {"error": "curso no encontrado"})

    try:
        cuerpo = validacion.leer_cuerpo(event)
    except validacion.EntradaInvalida as e:
        return _error_entrada(e)

    docs = [d for d in curso.get("documentos", []) if d.get("incluir", True)]
    contexto = "\n\n".join(
        f"[{d.get('nombre', 'documento')}]\n{d.get('texto', '')}" for d in docs
    )
    try:
        # Se valida antes de reservar cupo: una pregunta vacia no gasta el limite.
        ia_mod.validar_pregunta(cuerpo.get("pregunta"))
        if not _puede_usar_ia("chat", curso_id, event):
            return _respuesta(429, {"error": limites.MENSAJE_LIMITE})
        resultado = ia_mod.responder_pregunta(cuerpo.get("pregunta"), contexto)
    except ia_mod.EntradaInvalida as e:
        return _respuesta(400, {"error": str(e)})
    except ClientError as e:
        print("BEDROCK_ERROR", e.response.get("Error", {}).get("Code"))
        return _respuesta(502, {"error": "El modelo no está disponible ahora. Intenta de nuevo."})
    return _respuesta(200, {"respuesta": resultado["respuesta"], "fuente": resultado["fuente"]})


def _seleccionar_documentos(event, curso_id):
    """Marca que documentos entran en la ruta (incluir) y regenera la ruta."""
    curso = _leer_curso(curso_id)
    if curso is None:
        return _respuesta(404, {"error": "curso no encontrado"})

    try:
        cuerpo = validacion.leer_cuerpo(event)
    except validacion.EntradaInvalida as e:
        return _error_entrada(e)

    incluidos = cuerpo.get("incluidos")
    if not isinstance(incluidos, list):
        return _respuesta(400, {"error": "falta la lista 'incluidos' con los ids de documentos"})

    incluidos_set = set(incluidos)
    for d in curso.get("documentos", []):
        d["incluir"] = d["id"] in incluidos_set

    ruta_mod.regenerar(curso, limites.hoy_lima(), usar_ia=_puede_usar_ia("temas", curso_id, event))
    _guardar_curso(curso_id, curso)
    curso["id"] = curso_id
    return _respuesta(200, curso)


def _generar_plan(event, curso_id):
    """IA generativa (Bedrock Converse): redacta el plan de estudio del curso.

    Esta es la funcionalidad GenAI con proposito: explica/redacta el dato que el
    usuario acaba de registrar (su temario + ruta) dentro del flujo central.
    """
    curso = _leer_curso(curso_id)
    if curso is None:
        return _respuesta(404, {"error": "curso no encontrado"})

    try:
        ia_mod.validar_curso_para_plan(curso)
        if not _puede_usar_ia("plan", curso_id, event):
            return _respuesta(429, {"error": limites.MENSAJE_LIMITE})
        resultado = ia_mod.redactar_plan(curso)
    except ia_mod.EntradaInvalida as e:
        return _respuesta(400, {"error": str(e)})
    except ClientError as e:
        # Error no recuperable de Bedrock: 502, como el POST /mensaje del kit.
        print("BEDROCK_ERROR", e.response.get("Error", {}).get("Code"))
        return _respuesta(502, {"error": "El modelo no está disponible ahora. Intenta de nuevo."})

    # Se guarda el plan en el curso para no regenerarlo en cada visita.
    curso["plan"] = resultado["plan"]
    curso["planFuente"] = resultado["fuente"]
    _guardar_curso(curso_id, curso)
    return _respuesta(200, {"id": curso_id, "plan": resultado["plan"], "fuente": resultado["fuente"]})


def _recorrer_cursos(maximo=100):
    """Devuelve [(id, curso)] paginando el scan, hasta `maximo` cursos."""
    cursos = []
    clave_siguiente = None
    while True:
        kwargs = {}
        if clave_siguiente:
            kwargs["ExclusiveStartKey"] = clave_siguiente
        resultado = _tabla().scan(**kwargs)
        for it in resultado.get("Items", []):
            if it.get("tipo") == "curso":
                cursos.append((it["id"], json.loads(it["value"])))
        clave_siguiente = resultado.get("LastEvaluatedKey")
        if not clave_siguiente or len(cursos) >= maximo:
            break
    return cursos[:maximo]


def _listar_cursos():
    """Lista los espacios (sin el texto de los documentos, para no pesar)."""
    cursos = [
        {
            "id": cid,
            "nombre": c.get("nombre"),
            "fechaExamen": c.get("fechaExamen"),
            "totalDocumentos": len(c.get("documentos", [])),
            "totalTemas": len(c.get("temas", [])),
            "dias": c.get("ruta", {}).get("dias", 0),
            "ritmo": (c.get("riesgo") or {}).get("ritmo"),
        }
        for cid, c in _recorrer_cursos()
    ]
    return _respuesta(200, {"cursos": cursos})


# ===== Alerta temprana de abandono =====

MAX_DIAS_SIMULADOS = 60


def _hoy_simulado(valor):
    """Fecha de evaluacion. Por defecto hoy en Lima; la demo puede adelantarla
    (por ejemplo, para simular 3 dias sin actividad) hasta 60 dias."""
    real = limites.hoy_lima()
    if not valor:
        return real
    try:
        f = date.fromisoformat(str(valor))
    except ValueError:
        raise validacion.EntradaInvalida("'hoy' debe tener formato YYYY-MM-DD.")
    if not (real - timedelta(days=MAX_DIAS_SIMULADOS) <= f <= real + timedelta(days=MAX_DIAS_SIMULADOS)):
        raise validacion.EntradaInvalida(f"'hoy' debe estar a menos de {MAX_DIAS_SIMULADOS} dias de la fecha real.")
    return f


def _aplicar_evaluacion(curso, evaluacion, hoy):
    """Guarda la evaluacion y, si corresponde, replanifica la ruta. Devuelve el aviso o None."""
    aviso = None
    if evaluacion["debeReplanificar"]:
        aviso = ruta_mod.replanificar(curso, hoy)
        evaluacion["intervencion"]["avisoRuta"] = aviso
    riesgo_mod.guardar_evaluacion(curso, evaluacion)
    return aviso


def _registrar_actividad(event, curso_id):
    """POST /cursos/{id}/actividad: anota una sesion o respuestas y recalcula el riesgo."""
    curso = _leer_curso(curso_id)
    if curso is None:
        return _respuesta(404, {"error": "curso no encontrado"})
    try:
        cuerpo = validacion.leer_cuerpo(event)
        hoy = _hoy_simulado(cuerpo.get("hoy"))
        registro = riesgo_mod.registrar_actividad(curso, cuerpo, hoy)
    except validacion.EntradaInvalida as e:
        return _error_entrada(e)
    except riesgo_mod.ActividadInvalida as e:
        return _respuesta(400, {"error": str(e)})

    # Completar una sesion recalcula el riesgo del dia al momento (algorithms.md 6).
    evaluacion = riesgo_mod.evaluar(curso, hoy)
    _aplicar_evaluacion(curso, evaluacion, hoy)
    _guardar_curso(curso_id, curso)
    return _respuesta(201, {
        "actividad": registro,
        "ritmo": evaluacion["ritmo"],
        "nivel": evaluacion["nivel"],
        "intervencion": evaluacion["intervencion"],
    })


def _evaluar_riesgo(event, curso_id, aplicar):
    """GET (solo calcula) o POST (calcula, guarda y replanifica) /cursos/{id}/riesgo."""
    curso = _leer_curso(curso_id)
    if curso is None:
        return _respuesta(404, {"error": "curso no encontrado"})
    try:
        if aplicar:
            valor = validacion.leer_cuerpo(event).get("hoy")
        else:
            valor = (event.get("queryStringParameters") or {}).get("hoy")
        hoy = _hoy_simulado(valor)
    except validacion.EntradaInvalida as e:
        return _error_entrada(e)

    evaluacion = riesgo_mod.evaluar(curso, hoy)
    if aplicar:
        _aplicar_evaluacion(curso, evaluacion, hoy)
        _guardar_curso(curso_id, curso)
    evaluacion["id"] = curso_id
    if aplicar:
        evaluacion["ruta"] = curso["ruta"]
    return _respuesta(200, evaluacion)


def _evaluar_todos(hoy=None):
    """Tarea diaria (EventBridge): evalua el riesgo de cada curso y aplica la intervencion."""
    hoy = hoy or limites.hoy_lima()
    resumen = {"bajo": 0, "medio": 0, "alto": 0, "critico": 0, "replanificados": 0, "errores": 0}
    for curso_id, curso in _recorrer_cursos(maximo=1000):
        try:
            evaluacion = riesgo_mod.evaluar(curso, hoy)
            if _aplicar_evaluacion(curso, evaluacion, hoy):
                resumen["replanificados"] += 1
            _guardar_curso(curso_id, curso)
            resumen[evaluacion["nivel"]] += 1
        except (KeyError, TypeError, ValueError) as e:
            # Un curso con datos incompletos no frena la evaluacion del resto.
            print("RIESGO_ERROR", curso_id, type(e).__name__)
            resumen["errores"] += 1
    print("RIESGO_DIARIO", json.dumps(resumen))
    return resumen


def _ahora_epoch():
    import time as _t

    return _t.time()


def _crear_job(event):
    """Crea un trabajo asincrono. Se resuelve al leer (readyAt = ahora + 2s)."""
    try:
        cuerpo = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _respuesta(400, {"error": "cuerpo JSON invalido"})

    entrada = cuerpo.get("input")
    if entrada is None:
        return _respuesta(400, {"error": "falta el campo 'input'"})

    job_id = uuid.uuid4().hex
    item = {
        "id": "job#" + job_id,
        "tipo": "job",
        "value": json.dumps({"input": entrada, "readyAt": _ahora_epoch() + 2}),
    }
    _tabla().put_item(Item=item)
    return _respuesta(202, {"jobId": job_id})


def _obtener_job(job_id):
    """Devuelve el estado del trabajo. Si ya paso readyAt, status=done y output invertido."""
    resultado = _tabla().get_item(Key={"id": "job#" + job_id})
    item = resultado.get("Item")
    if not item or item.get("tipo") != "job":
        return _respuesta(404, {"error": "job no encontrado"})

    datos = json.loads(item["value"])
    entrada = datos.get("input", "")
    if _ahora_epoch() >= datos.get("readyAt", 0):
        # input al reves, caracter por caracter: "abc1" -> "1cba"
        salida = entrada[::-1] if isinstance(entrada, str) else entrada
        return _respuesta(200, {"jobId": job_id, "status": "done", "output": salida})
    return _respuesta(200, {"jobId": job_id, "status": "queued", "output": None})


def _pumpkin(event):
    """GET /pumpkin?nonce=<palabra> -> {pumpkin: palabra al reves, team}."""
    params = event.get("queryStringParameters") or {}
    palabra = params.get("nonce", "")
    return _respuesta(200, {"pumpkin": palabra[::-1], "team": TEAM_ID})


def _exorcise(event):
    """POST /exorcise {items:[...]} -> items sin duplicados, orden de primera aparicion."""
    try:
        cuerpo = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _respuesta(400, {"error": "cuerpo JSON invalido"})

    items = cuerpo.get("items")
    if not isinstance(items, list):
        return _respuesta(400, {"error": "falta la lista 'items'"})

    vistos = set()
    unicos = []
    for it in items:
        # Clave que soporta valores no hashables (dict/list) via su JSON.
        clave = it if isinstance(it, (str, int, float, bool, type(None))) else json.dumps(it, sort_keys=True)
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(it)
    return _respuesta(200, {"items": unicos})


_DIAS_ES = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


def _conjuro(event):
    """POST /conjuro {dates:[YYYY-MM-DD]} -> weekdays en espanol, minusculas."""
    from datetime import date as _date

    try:
        cuerpo = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _respuesta(400, {"error": "cuerpo JSON invalido"})

    fechas = cuerpo.get("dates")
    if not isinstance(fechas, list):
        return _respuesta(400, {"error": "falta la lista 'dates'"})

    dias = []
    for f in fechas:
        try:
            d = _date.fromisoformat(str(f))
            dias.append(_DIAS_ES[d.weekday()])
        except (TypeError, ValueError):
            return _respuesta(400, {"error": f"fecha invalida: {f}"})
    return _respuesta(200, {"weekdays": dias})


_TIPOS_WEB = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".ico": "image/x-icon",
}


def _servir_web(ruta):
    """GET /app y /app/<archivo>: sirve el prototipo web desde WEB_DIR (capa en /opt)."""
    import base64

    base = os.path.realpath(os.environ.get("WEB_DIR", "/opt"))
    relativo = ruta[len("/app"):].lstrip("/") or "index.html"
    destino = os.path.realpath(os.path.join(base, relativo))
    extension = os.path.splitext(destino)[1].lower()
    # Evita salir de la carpeta (../) y servir archivos que no son del frontend.
    if not destino.startswith(base + os.sep) or extension not in _TIPOS_WEB or not os.path.isfile(destino):
        return _respuesta(404, {"error": "ruta no encontrada"})

    with open(destino, "rb") as f:
        contenido = f.read()
    tipo = _TIPOS_WEB[extension]
    headers = {"content-type": tipo, "cache-control": "no-cache"}

    if extension == ".html":
        # Con <base href="/app/"> los enlaces relativos (estilos.css, subir.html) funcionan desde /app.
        html = contenido.decode("utf-8").replace("<head>", '<head>\n  <base href="/app/" />', 1)
        return {"statusCode": 200, "headers": headers, "body": html}
    if tipo.startswith("image/"):
        return {
            "statusCode": 200,
            "headers": headers,
            "body": base64.b64encode(contenido).decode("ascii"),
            "isBase64Encoded": True,
        }
    return {"statusCode": 200, "headers": headers, "body": contenido.decode("utf-8")}


def handler(event, context=None):
    """Punto de entrada de la Lambda. Enruta segun metodo y ruta."""
    # Evento programado de EventBridge (template.yaml, RiesgoDiario).
    if event.get("source") == "aws.events" or event.get("tarea") == "evaluar-riesgo":
        return _evaluar_todos()

    metodo, ruta = _metodo_y_ruta(event)

    if metodo == "GET" and (ruta == "/app" or ruta.startswith("/app/")):
        return _servir_web(ruta)

    if metodo == "GET" and ruta == "/health":
        return _respuesta(200, {"status": "ok", "team": TEAM_ID})

    if ruta == "/items" and metodo == "POST":
        return _crear_item(event)

    if ruta == "/items" and metodo == "GET":
        return _listar_items()

    if ruta.startswith("/items/") and metodo == "GET":
        item_id = _id_de_ruta(event, ruta)
        if not item_id:
            return _respuesta(400, {"error": "falta el id"})
        return _obtener_item(item_id)

    if ruta == "/cursos" and metodo == "POST":
        return _crear_curso(event)

    if ruta == "/cursos" and metodo == "GET":
        return _listar_cursos()

    # /cursos/{id}/documentos  -> POST agrega documentos, PUT actualiza seleccion
    if ruta.startswith("/cursos/") and ruta.endswith("/documentos") and metodo in ("POST", "PUT"):
        curso_id = (event.get("pathParameters") or {}).get("id")
        if not curso_id:
            partes = ruta.split("/")
            curso_id = partes[2] if len(partes) >= 4 else None
        if not curso_id:
            return _respuesta(400, {"error": "falta el id"})
        if metodo == "PUT":
            return _seleccionar_documentos(event, curso_id)
        return _agregar_documentos(event, curso_id)

    # POST /cursos/{id}/chat  -> chat con IA sobre los documentos
    if ruta.startswith("/cursos/") and ruta.endswith("/chat") and metodo == "POST":
        curso_id = (event.get("pathParameters") or {}).get("id")
        if not curso_id:
            partes = ruta.split("/")
            curso_id = partes[2] if len(partes) >= 4 else None
        if not curso_id:
            return _respuesta(400, {"error": "falta el id"})
        return _chat_curso(event, curso_id)

    # POST /cursos/{id}/plan  -> IA generativa: redacta el plan de estudio
    if ruta.startswith("/cursos/") and ruta.endswith("/plan") and metodo == "POST":
        curso_id = (event.get("pathParameters") or {}).get("id")
        if not curso_id:
            partes = ruta.split("/")
            curso_id = partes[2] if len(partes) >= 4 else None
        if not curso_id:
            return _respuesta(400, {"error": "falta el id"})
        return _generar_plan(event, curso_id)

    # /cursos/{id}/actividad y /cursos/{id}/riesgo -> alerta temprana de abandono
    if ruta.startswith("/cursos/") and ruta.endswith(("/actividad", "/riesgo")):
        partes = ruta.split("/")
        curso_id = (event.get("pathParameters") or {}).get("id") or (partes[2] if len(partes) >= 4 else None)
        if not curso_id:
            return _respuesta(400, {"error": "falta el id"})
        if ruta.endswith("/actividad") and metodo == "POST":
            return _registrar_actividad(event, curso_id)
        if ruta.endswith("/riesgo") and metodo in ("GET", "POST"):
            return _evaluar_riesgo(event, curso_id, aplicar=(metodo == "POST"))
        return _respuesta(404, {"error": "ruta no encontrada"})

    if ruta.startswith("/cursos/") and metodo == "GET":
        partes = ruta.split("/")
        curso_id = (event.get("pathParameters") or {}).get("id") or (partes[2] if len(partes) >= 3 else None)
        if not curso_id:
            return _respuesta(400, {"error": "falta el id"})
        return _obtener_curso(curso_id)

    # Trabajos asincronos (insignia "Asincrono o agente")
    if ruta == "/jobs" and metodo == "POST":
        return _crear_job(event)

    if ruta.startswith("/jobs/") and metodo == "GET":
        partes = ruta.split("/")
        job_id = (event.get("pathParameters") or {}).get("jobId") or (partes[2] if len(partes) >= 3 else None)
        if not job_id:
            return _respuesta(400, {"error": "falta el jobId"})
        return _obtener_job(job_id)

    # Retos de Halloween
    if ruta == "/pumpkin" and metodo == "GET":
        return _pumpkin(event)

    if ruta == "/exorcise" and metodo == "POST":
        return _exorcise(event)

    if ruta == "/conjuro" and metodo == "POST":
        return _conjuro(event)

    return _respuesta(404, {"error": "ruta no encontrada"})
