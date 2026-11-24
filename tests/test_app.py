"""Pruebas del contrato de la insignia "Persistencia": /items.

Usan una tabla falsa en memoria (monkeypatch de app.TABLE) para no tocar
DynamoDB real.
"""

import json
import os

os.environ.setdefault("TEAM_ID", "T034")
os.environ.setdefault("TABLE_NAME", "tabla-falsa")

from datetime import date, timedelta

import pytest
from botocore.exceptions import ClientError

import app
import ia as _ia_detector


@pytest.fixture(autouse=True)
def _sin_bedrock_en_deteccion(monkeypatch):
    # La deteccion de temas cae a la heuristica local en las pruebas (sin red).
    monkeypatch.setattr(_ia_detector, "detectar_temas_ia", lambda *_a, **_k: None)


class TablaFalsa:
    """Doble de una tabla DynamoDB con la minima API que usa app.py."""

    def __init__(self):
        self.datos = {}

    def put_item(self, Item):
        self.datos[Item["id"]] = dict(Item)
        return {}

    def get_item(self, Key):
        item = self.datos.get(Key["id"])
        return {"Item": dict(item)} if item else {}

    def update_item(self, Key, UpdateExpression, ConditionExpression, ExpressionAttributeValues):
        # Solo el patron de limites.py: SET tipo, expira ADD conteo, con tope condicional.
        valores = ExpressionAttributeValues
        item = self.datos.setdefault(Key["id"], {"id": Key["id"]})
        if item.get("conteo", 0) >= valores[":maximo"]:
            raise ClientError({"Error": {"Code": "ConditionalCheckFailedException", "Message": "lleno"}}, "UpdateItem")
        item.update({"tipo": valores[":tipo"], "expira": valores[":expira"]})
        item["conteo"] = item.get("conteo", 0) + valores[":uno"]
        return {}

    def scan(self, **kwargs):
        # Ignora la paginacion: devuelve todo de una, sin LastEvaluatedKey.
        return {"Items": list(self.datos.values())}


# Fecha de examen relativa: la API rechaza examenes a mas de un anio.
FECHA_EXAMEN = (date.today() + timedelta(days=30)).isoformat()


def _evento(metodo, ruta, body=None, path_params=None):
    return {
        "requestContext": {"http": {"method": metodo, "path": ruta}},
        "rawPath": ruta,
        "pathParameters": path_params,
        "body": json.dumps(body) if body is not None else None,
    }


def setup_function(_):
    # Antes de cada prueba: tabla limpia.
    app.TABLE = TablaFalsa()


def test_crear_item_devuelve_id_y_valor():
    respuesta = app.handler(_evento("POST", "/items", {"value": "nonce-123"}))

    assert respuesta["statusCode"] in (200, 201)
    cuerpo = json.loads(respuesta["body"])
    assert cuerpo["value"] == "nonce-123"
    assert cuerpo["id"]


def test_obtener_item_por_id():
    creado = json.loads(
        app.handler(_evento("POST", "/items", {"value": "abc"}))["body"]
    )
    item_id = creado["id"]

    respuesta = app.handler(
        _evento("GET", f"/items/{item_id}", path_params={"id": item_id})
    )
    assert respuesta["statusCode"] == 200
    cuerpo = json.loads(respuesta["body"])
    assert cuerpo == {"id": item_id, "value": "abc"}


def test_obtener_item_inexistente_da_404():
    respuesta = app.handler(
        _evento("GET", "/items/no-existe", path_params={"id": "no-existe"})
    )
    assert respuesta["statusCode"] == 404


def test_listar_items_incluye_el_recien_creado():
    creado = json.loads(
        app.handler(_evento("POST", "/items", {"value": "en-la-lista"}))["body"]
    )

    respuesta = app.handler(_evento("GET", "/items"))
    assert respuesta["statusCode"] == 200
    cuerpo = json.loads(respuesta["body"])
    items = cuerpo["items"] if isinstance(cuerpo, dict) else cuerpo
    ids = [i["id"] for i in items]
    assert creado["id"] in ids


def test_crear_item_sin_value_da_400():
    respuesta = app.handler(_evento("POST", "/items", {}))
    assert respuesta["statusCode"] == 400


TEXTO_PDF = (
    "Capitulo 1: Cinematica. La velocidad es el cambio de posicion en el tiempo. "
    "Capitulo 2: Leyes de Newton. La segunda ley establece que F = m por a."
)


def test_crear_curso_con_varios_documentos():
    resp = app.handler(
        _evento("POST", "/cursos", {
            "nombre": "Física I",
            "documentos": [
                {"nombre": "cap1.pdf", "texto": TEXTO_PDF},
                {"nombre": "cap2.pdf", "texto": "Capitulo 3: Energia. El trabajo es fuerza por distancia recorrida."},
            ],
            "fechaExamen": FECHA_EXAMEN, "minutosPorDia": 60,
        })
    )
    assert resp["statusCode"] == 201
    curso = json.loads(resp["body"])
    assert curso["id"]
    assert len(curso["documentos"]) == 2
    assert curso["ruta"]["sesiones"]


def test_crear_curso_formato_antiguo_un_texto():
    # Compatibilidad: {texto} sigue funcionando.
    resp = app.handler(_evento("POST", "/cursos", {"nombre": "X", "texto": TEXTO_PDF, "fechaExamen": FECHA_EXAMEN}))
    assert resp["statusCode"] == 201


def test_crear_curso_sin_texto_da_400():
    resp = app.handler(_evento("POST", "/cursos", {"documentos": [{"nombre": "x", "texto": "corto"}]}))
    assert resp["statusCode"] == 400


def test_agregar_documentos_regenera_la_ruta():
    creado = json.loads(
        app.handler(_evento("POST", "/cursos", {
            "nombre": "Cálculo", "texto": TEXTO_PDF, "fechaExamen": FECHA_EXAMEN,
        }))["body"]
    )
    cid = creado["id"]
    resp = app.handler(_evento("POST", f"/cursos/{cid}/documentos", {
        "documentos": [{"nombre": "cap2.pdf", "texto": "Capitulo 3: Energia. El trabajo es fuerza por distancia."}],
    }, path_params={"id": cid}))
    assert resp["statusCode"] == 200
    curso = json.loads(resp["body"])
    assert len(curso["documentos"]) == 2


def test_agregar_documentos_a_curso_inexistente_da_404():
    resp = app.handler(_evento("POST", "/cursos/no-existe/documentos", {
        "documentos": [{"nombre": "x", "texto": TEXTO_PDF}],
    }, path_params={"id": "no-existe"}))
    assert resp["statusCode"] == 404


def test_obtener_curso_devuelve_la_ruta():
    creado = json.loads(
        app.handler(_evento("POST", "/cursos", {
            "nombre": "Cálculo", "texto": TEXTO_PDF, "fechaExamen": FECHA_EXAMEN,
        }))["body"]
    )
    resp = app.handler(_evento("GET", f"/cursos/{creado['id']}", path_params={"id": creado["id"]}))
    assert resp["statusCode"] == 200
    curso = json.loads(resp["body"])
    assert curso["nombre"] == "Cálculo"


def test_listar_cursos():
    app.handler(_evento("POST", "/cursos", {"nombre": "Uno", "texto": TEXTO_PDF, "fechaExamen": FECHA_EXAMEN}))
    resp = app.handler(_evento("GET", "/cursos"))
    assert resp["statusCode"] == 200
    datos = json.loads(resp["body"])
    assert "cursos" in datos
    assert any(c["nombre"] == "Uno" for c in datos["cursos"])


# ===== IA generativa con proposito (Bedrock Converse) =====

import ia as ia_mod
from botocore.exceptions import ClientError


class BedrockFalso:
    """Doble del cliente bedrock-runtime. Controla la respuesta de converse()."""

    def __init__(self, texto="Tu plan esta listo: vas a dominar los temas clave. ¡Vamos!", error=None, falla_veces=0):
        self.texto = texto
        self.error = error  # un ClientError a lanzar
        self.falla_veces = falla_veces  # nº de ThrottlingException antes de responder
        self.llamadas = 0

    def converse(self, **kwargs):
        self.llamadas += 1
        if self.error is not None:
            raise self.error
        if self.llamadas <= self.falla_veces:
            raise ClientError({"Error": {"Code": "ThrottlingException", "Message": "slow down"}}, "Converse")
        return {"output": {"message": {"content": [{"text": self.texto}]}}}


def _crear_curso_para_plan():
    creado = json.loads(
        app.handler(_evento("POST", "/cursos", {
            "nombre": "Física I", "texto": TEXTO_PDF, "fechaExamen": FECHA_EXAMEN,
        }))["body"]
    )
    return creado["id"]


def test_plan_usa_bedrock(monkeypatch):
    cid = _crear_curso_para_plan()
    falso = BedrockFalso(texto="Tu plan para Física I está listo: 3 temas en varios días. Empieza por lo esencial y avanza un poco cada día.")
    monkeypatch.setattr(ia_mod, "BEDROCK", falso)
    resp = app.handler(_evento("POST", f"/cursos/{cid}/plan", {}, path_params={"id": cid}))
    assert resp["statusCode"] == 200
    datos = json.loads(resp["body"])
    assert datos["fuente"] == "bedrock"
    assert "Física I" in datos["plan"]
    assert falso.llamadas == 1


def test_plan_reintenta_ante_throttling(monkeypatch):
    cid = _crear_curso_para_plan()
    # Falla 2 veces con throttling y a la tercera responde.
    falso = BedrockFalso(texto="Plan listo. Vamos con constancia.", falla_veces=2)
    monkeypatch.setattr(ia_mod, "BEDROCK", falso)
    monkeypatch.setattr(ia_mod.time, "sleep", lambda *_: None)  # sin esperas reales
    resp = app.handler(_evento("POST", f"/cursos/{cid}/plan", {}, path_params={"id": cid}))
    assert resp["statusCode"] == 200
    datos = json.loads(resp["body"])
    assert datos["fuente"] == "bedrock"
    assert falso.llamadas == 3


def test_plan_usa_respaldo_si_throttling_persiste(monkeypatch):
    cid = _crear_curso_para_plan()
    falso = BedrockFalso(falla_veces=99)  # siempre throttling
    monkeypatch.setattr(ia_mod, "BEDROCK", falso)
    monkeypatch.setattr(ia_mod.time, "sleep", lambda *_: None)
    resp = app.handler(_evento("POST", f"/cursos/{cid}/plan", {}, path_params={"id": cid}))
    # El flujo NO se rompe: responde 200 con el plan de respaldo.
    assert resp["statusCode"] == 200
    datos = json.loads(resp["body"])
    assert datos["fuente"] == "respaldo"
    assert datos["plan"]


def test_plan_error_no_recuperable_da_502(monkeypatch):
    cid = _crear_curso_para_plan()
    err = ClientError({"Error": {"Code": "AccessDeniedException", "Message": "no"}}, "Converse")
    falso = BedrockFalso(error=err)
    monkeypatch.setattr(ia_mod, "BEDROCK", falso)
    resp = app.handler(_evento("POST", f"/cursos/{cid}/plan", {}, path_params={"id": cid}))
    assert resp["statusCode"] == 502


def test_plan_curso_inexistente_da_404(monkeypatch):
    monkeypatch.setattr(ia_mod, "BEDROCK", BedrockFalso())
    resp = app.handler(_evento("POST", "/cursos/no-existe/plan", {}, path_params={"id": "no-existe"}))
    assert resp["statusCode"] == 404


# ===== Chat con IA sobre los documentos =====

def test_chat_responde_con_bedrock(monkeypatch):
    cid = _crear_curso_para_plan()
    monkeypatch.setattr(ia_mod, "BEDROCK", BedrockFalso(texto="La segunda ley dice F = m·a."))
    resp = app.handler(_evento("POST", f"/cursos/{cid}/chat", {"pregunta": "¿Qué dice la 2da ley?"}, path_params={"id": cid}))
    assert resp["statusCode"] == 200
    datos = json.loads(resp["body"])
    assert datos["fuente"] == "bedrock"
    assert "F = m" in datos["respuesta"]


def test_chat_sin_pregunta_da_400(monkeypatch):
    cid = _crear_curso_para_plan()
    monkeypatch.setattr(ia_mod, "BEDROCK", BedrockFalso())
    resp = app.handler(_evento("POST", f"/cursos/{cid}/chat", {"pregunta": "  "}, path_params={"id": cid}))
    assert resp["statusCode"] == 400


def test_chat_curso_inexistente_da_404(monkeypatch):
    monkeypatch.setattr(ia_mod, "BEDROCK", BedrockFalso())
    resp = app.handler(_evento("POST", "/cursos/no-existe/chat", {"pregunta": "hola"}, path_params={"id": "no-existe"}))
    assert resp["statusCode"] == 404


# ===== Seleccion de documentos que entran en la ruta =====

def test_seleccionar_documentos_regenera(monkeypatch):
    # Curso con 2 documentos.
    creado = json.loads(app.handler(_evento("POST", "/cursos", {
        "nombre": "Física", "fechaExamen": FECHA_EXAMEN,
        "documentos": [
            {"nombre": "a.pdf", "texto": "Capitulo 1: Cinematica. La velocidad es cambio de posicion."},
            {"nombre": "b.pdf", "texto": "Capitulo 2: Energia. El trabajo es fuerza por distancia."},
        ],
    }))["body"])
    cid = creado["id"]
    ids = [d["id"] for d in creado["documentos"]]

    # Incluir solo el primero.
    resp = app.handler(_evento("PUT", f"/cursos/{cid}/documentos", {"incluidos": [ids[0]]}, path_params={"id": cid}))
    assert resp["statusCode"] == 200
    curso = json.loads(resp["body"])
    incluidos = {d["id"]: d["incluir"] for d in curso["documentos"]}
    assert incluidos[ids[0]] is True
    assert incluidos[ids[1]] is False


def test_seleccionar_sin_lista_da_400():
    creado = json.loads(app.handler(_evento("POST", "/cursos", {"nombre": "X", "texto": TEXTO_PDF, "fechaExamen": FECHA_EXAMEN}))["body"])
    resp = app.handler(_evento("PUT", f"/cursos/{creado['id']}/documentos", {}, path_params={"id": creado["id"]}))
    assert resp["statusCode"] == 400


# ===== Jobs asincronos (insignia "Asincrono o agente") =====

def test_crear_job_responde_202_con_jobid():
    resp = app.handler(_evento("POST", "/jobs", {"input": "abc1"}))
    assert resp["statusCode"] in (200, 201, 202)
    datos = json.loads(resp["body"])
    assert datos["jobId"]


def test_crear_job_sin_input_da_400():
    resp = app.handler(_evento("POST", "/jobs", {}))
    assert resp["statusCode"] == 400


def test_job_recien_creado_esta_queued(monkeypatch):
    # Reloj congelado: aun no llega readyAt.
    monkeypatch.setattr(app, "_ahora_epoch", lambda: 1000.0)
    jid = json.loads(app.handler(_evento("POST", "/jobs", {"input": "abc1"}))["body"])["jobId"]
    resp = app.handler(_evento("GET", f"/jobs/{jid}", path_params={"jobId": jid}))
    datos = json.loads(resp["body"])
    assert resp["statusCode"] == 200
    assert datos["status"] == "queued"


def test_job_despues_de_readyat_esta_done(monkeypatch):
    # Creado en t=1000 (readyAt=1002); se consulta en t=1003 -> done.
    monkeypatch.setattr(app, "_ahora_epoch", lambda: 1000.0)
    jid = json.loads(app.handler(_evento("POST", "/jobs", {"input": "abc1"}))["body"])["jobId"]
    monkeypatch.setattr(app, "_ahora_epoch", lambda: 1003.0)
    resp = app.handler(_evento("GET", f"/jobs/{jid}", path_params={"jobId": jid}))
    datos = json.loads(resp["body"])
    assert datos["status"] == "done"
    assert datos["output"] == "1cba"  # "abc1" al reves


def test_job_inexistente_da_404():
    resp = app.handler(_evento("GET", "/jobs/no-existe", path_params={"jobId": "no-existe"}))
    assert resp["statusCode"] == 404


# ===== Retos de Halloween =====

def test_pumpkin_invierte_y_devuelve_team():
    ev = {"requestContext": {"http": {"method": "GET", "path": "/pumpkin"}}, "rawPath": "/pumpkin", "queryStringParameters": {"nonce": "bruja"}}
    app.TEAM_ID = "T034"
    resp = app.handler(ev)
    datos = json.loads(resp["body"])
    assert datos == {"pumpkin": "ajurb", "team": "T034"}


def test_exorcise_quita_duplicados_conserva_orden():
    resp = app.handler(_evento("POST", "/exorcise", {"items": ["a", "b", "a", "c", "b", "d"]}))
    datos = json.loads(resp["body"])
    assert datos["items"] == ["a", "b", "c", "d"]


def test_exorcise_con_numeros_y_repetidos():
    resp = app.handler(_evento("POST", "/exorcise", {"items": [1, 1, 2, 3, 2, 1]}))
    assert json.loads(resp["body"])["items"] == [1, 2, 3]


def test_conjuro_dias_en_espanol():
    resp = app.handler(_evento("POST", "/conjuro", {"dates": ["2026-10-31", "2026-11-01", "2026-10-30"]}))
    datos = json.loads(resp["body"])
    # 31 oct 2026 = sabado, 1 nov = domingo, 30 oct = viernes
    assert datos["weekdays"] == ["sabado", "domingo", "viernes"]


def test_conjuro_fecha_invalida_da_400():
    resp = app.handler(_evento("POST", "/conjuro", {"dates": ["no-es-fecha"]}))
    assert resp["statusCode"] == 400


# ===== Validacion de entrada en /cursos =====

def _crear(cuerpo):
    return app.handler(_evento("POST", "/cursos", cuerpo))


def test_crear_curso_rechaza_archivo_que_no_es_pdf():
    resp = _crear({"nombre": "X", "fechaExamen": FECHA_EXAMEN, "documentos": [{"nombre": "notas.docx", "texto": TEXTO_PDF}]})
    assert resp["statusCode"] == 400
    assert "PDF" in json.loads(resp["body"])["error"]


def test_crear_curso_rechaza_demasiados_documentos():
    docs = [{"nombre": f"d{i}.pdf", "texto": TEXTO_PDF} for i in range(11)]
    resp = _crear({"nombre": "X", "fechaExamen": FECHA_EXAMEN, "documentos": docs})
    assert resp["statusCode"] == 400


def test_crear_curso_rechaza_documento_demasiado_extenso():
    resp = _crear({"nombre": "X", "fechaExamen": FECHA_EXAMEN, "documentos": [{"nombre": "a.pdf", "texto": "a " * 70_000}]})
    assert resp["statusCode"] == 413


def test_crear_curso_rechaza_cuerpo_mayor_a_1_mb():
    ev = _evento("POST", "/cursos")
    ev["body"] = json.dumps({"documentos": [{"nombre": "a.pdf", "texto": "x" * 1_100_000}]})
    assert app.handler(ev)["statusCode"] == 413


def test_crear_curso_rechaza_texto_binario():
    binario = "".join(chr(i % 32) for i in range(2000))
    resp = _crear({"nombre": "X", "fechaExamen": FECHA_EXAMEN, "documentos": [{"nombre": "a.pdf", "texto": binario}]})
    assert resp["statusCode"] == 400


@pytest.mark.parametrize("minutos", [0, 5, 1000, "mucho", True])
def test_crear_curso_rechaza_minutos_invalidos(minutos):
    resp = _crear({"nombre": "X", "texto": TEXTO_PDF, "fechaExamen": FECHA_EXAMEN, "minutosPorDia": minutos})
    assert resp["statusCode"] == 400


@pytest.mark.parametrize("fecha", ["2020-01-01", "31/12/2026", "2099-12-31"])
def test_crear_curso_rechaza_fecha_invalida(fecha):
    resp = _crear({"nombre": "X", "texto": TEXTO_PDF, "fechaExamen": fecha})
    assert resp["statusCode"] == 400


def test_crear_curso_sin_fecha_usa_10_dias():
    resp = _crear({"nombre": "X", "texto": TEXTO_PDF, "fechaExamen": ""})
    assert resp["statusCode"] == 201


def test_agregar_documentos_respeta_maximo_por_curso():
    docs = [{"nombre": f"d{i}.pdf", "texto": TEXTO_PDF} for i in range(9)]
    cid = json.loads(_crear({"nombre": "X", "fechaExamen": FECHA_EXAMEN, "documentos": docs})["body"])["id"]
    extra = [{"nombre": "e1.pdf", "texto": TEXTO_PDF}, {"nombre": "e2.pdf", "texto": TEXTO_PDF}]
    resp = app.handler(_evento("POST", f"/cursos/{cid}/documentos", {"documentos": extra}, path_params={"id": cid}))
    assert resp["statusCode"] == 400


# ===== Limites diarios de IA =====

import limites


def test_chat_responde_429_al_agotar_el_cupo(monkeypatch):
    cid = _crear_curso_para_plan()
    falso = BedrockFalso(texto="Respuesta.")
    monkeypatch.setattr(ia_mod, "BEDROCK", falso)
    monkeypatch.setitem(limites.LIMITES, "chat", 2)
    codigos = [
        app.handler(_evento("POST", f"/cursos/{cid}/chat", {"pregunta": "hola"}, path_params={"id": cid}))["statusCode"]
        for _ in range(3)
    ]
    assert codigos == [200, 200, 429]
    assert falso.llamadas == 2  # la tercera no llega a Bedrock


def test_pregunta_vacia_no_gasta_cupo(monkeypatch):
    cid = _crear_curso_para_plan()
    monkeypatch.setattr(ia_mod, "BEDROCK", BedrockFalso())
    monkeypatch.setitem(limites.LIMITES, "chat", 1)
    app.handler(_evento("POST", f"/cursos/{cid}/chat", {"pregunta": " "}, path_params={"id": cid}))
    resp = app.handler(_evento("POST", f"/cursos/{cid}/chat", {"pregunta": "hola"}, path_params={"id": cid}))
    assert resp["statusCode"] == 200


def test_plan_responde_429_con_cupo_global_agotado(monkeypatch):
    cid = _crear_curso_para_plan()
    monkeypatch.setattr(ia_mod, "BEDROCK", BedrockFalso())
    monkeypatch.setitem(limites.LIMITES, "global", 0)
    resp = app.handler(_evento("POST", f"/cursos/{cid}/plan", {}, path_params={"id": cid}))
    assert resp["statusCode"] == 429


def test_deteccion_de_temas_usa_heuristica_si_no_hay_cupo(monkeypatch):
    llamadas = []
    monkeypatch.setattr(_ia_detector, "detectar_temas_ia", lambda *a, **k: llamadas.append(1))
    monkeypatch.setitem(limites.LIMITES, "ip", 0)
    ev = _evento("POST", "/cursos", {"nombre": "X", "texto": TEXTO_PDF, "fechaExamen": FECHA_EXAMEN})
    ev["requestContext"]["http"]["sourceIp"] = "203.0.113.7"
    resp = app.handler(ev)
    assert resp["statusCode"] == 201
    assert json.loads(resp["body"])["temasFuente"] == "heuristica"
    assert llamadas == []


def test_contadores_de_limites_no_aparecen_en_items(monkeypatch):
    cid = _crear_curso_para_plan()
    monkeypatch.setattr(ia_mod, "BEDROCK", BedrockFalso())
    app.handler(_evento("POST", f"/cursos/{cid}/chat", {"pregunta": "hola"}, path_params={"id": cid}))
    items = json.loads(app.handler(_evento("GET", "/items"))["body"])["items"]
    assert not any(str(i["id"]).startswith("limite#") for i in items)


# ===== Alerta temprana de abandono =====

def _curso_con_ruta():
    return json.loads(_crear({"nombre": "Física I", "texto": TEXTO_PDF, "fechaExamen": FECHA_EXAMEN, "minutosPorDia": 30})["body"])


def test_riesgo_de_curso_nuevo_es_bajo():
    curso = _curso_con_ruta()
    resp = app.handler(_evento("GET", f"/cursos/{curso['id']}/riesgo", path_params={"id": curso["id"]}))
    assert resp["statusCode"] == 200
    datos = json.loads(resp["body"])
    assert datos["nivel"] == "bajo"
    assert datos["ritmo"]["emoji"] == "🟢"
    assert {f["nombre"] for f in datos["factores"]} == {
        "inactividad", "atraso", "caida_aciertos", "sesiones_a_medias", "presion_examen",
    }


def test_simular_dias_sin_actividad_sube_el_riesgo_y_reorganiza_la_ruta():
    curso = _curso_con_ruta()
    cid = curso["id"]
    primera = curso["ruta"]["sesiones"][0]["fecha"]
    app.handler(_evento("POST", f"/cursos/{cid}/actividad", {"evento": "sesion_completada", "fechaSesion": primera}, path_params={"id": cid}))

    futuro = (date.fromisoformat(curso["creadoEn"]) + timedelta(days=4)).isoformat()
    resp = app.handler(_evento("POST", f"/cursos/{cid}/riesgo", {"hoy": futuro}, path_params={"id": cid}))
    assert resp["statusCode"] == 200
    datos = json.loads(resp["body"])
    assert datos["nivel"] in ("medio", "alto", "critico")
    assert datos["intervencion"]["avisoRuta"].startswith("Reorganizamos tu ruta")
    assert datos["ruta"]["version"] == 2

    guardado = json.loads(app.handler(_evento("GET", f"/cursos/{cid}", path_params={"id": cid}))["body"])
    assert guardado["riesgo"]["nivel"] == datos["nivel"]
    assert guardado["historialRiesgo"][-1]["fecha"] == futuro


def test_registrar_actividad_invalida_da_400():
    cid = _curso_con_ruta()["id"]
    resp = app.handler(_evento("POST", f"/cursos/{cid}/actividad", {"evento": "dormir"}, path_params={"id": cid}))
    assert resp["statusCode"] == 400


def test_riesgo_rechaza_fecha_simulada_lejana():
    cid = _curso_con_ruta()["id"]
    resp = app.handler(_evento("POST", f"/cursos/{cid}/riesgo", {"hoy": "2030-01-01"}, path_params={"id": cid}))
    assert resp["statusCode"] == 400


def test_riesgo_curso_inexistente_da_404():
    resp = app.handler(_evento("GET", "/cursos/no-existe/riesgo", path_params={"id": "no-existe"}))
    assert resp["statusCode"] == 404


def test_evento_programado_evalua_todos_los_cursos():
    _curso_con_ruta()
    _curso_con_ruta()
    resumen = app.handler({"tarea": "evaluar-riesgo"})
    assert resumen["bajo"] == 2
    assert resumen["errores"] == 0
    cursos = json.loads(app.handler(_evento("GET", "/cursos"))["body"])["cursos"]
    assert all(c["ritmo"]["texto"] == "Vas a buen ritmo" for c in cursos)
