"""Prueba del contrato de la insignia "API viva": GET /health."""

import json
import os

os.environ.setdefault("TEAM_ID", "T034")
os.environ.setdefault("TABLE_NAME", "tabla-falsa")

import app


def _evento(metodo, ruta, body=None):
    """Evento minimo con el formato de HTTP API (payload v2)."""
    return {
        "requestContext": {"http": {"method": metodo, "path": ruta}},
        "rawPath": ruta,
        "body": json.dumps(body) if body is not None else None,
    }


def test_health_responde_ok_con_el_team():
    app.TEAM_ID = "T034"
    respuesta = app.handler(_evento("GET", "/health"))

    assert respuesta["statusCode"] == 200
    assert respuesta["headers"]["content-type"] == "application/json"

    cuerpo = json.loads(respuesta["body"])
    assert cuerpo == {"status": "ok", "team": "T034"}


def test_health_es_publica_y_no_pide_autenticacion():
    # El evento no lleva cabeceras de autorizacion y aun asi responde 200.
    respuesta = app.handler(_evento("GET", "/health"))
    assert respuesta["statusCode"] == 200
