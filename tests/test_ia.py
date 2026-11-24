"""Pruebas del modulo de IA generativa (src/ia.py) con Bedrock simulado."""

import os

os.environ.setdefault("TEAM_ID", "T034")
os.environ.setdefault("TABLE_NAME", "tabla-falsa")

import ia as ia_mod
from botocore.exceptions import ClientError


class BedrockFalso:
    def __init__(self, texto="Plan listo.", error=None, falla_veces=0):
        self.texto = texto
        self.error = error
        self.falla_veces = falla_veces
        self.llamadas = 0

    def converse(self, **kwargs):
        self.llamadas += 1
        if self.error is not None:
            raise self.error
        if self.llamadas <= self.falla_veces:
            raise ClientError({"Error": {"Code": "ThrottlingException", "Message": "x"}}, "Converse")
        return {"output": {"message": {"content": [{"text": self.texto}]}}}


CURSO = {
    "nombre": "Física I",
    "ruta": {"dias": 10, "modoRescate": False},
    "temas": [
        {"nombre": "Cinemática", "importancia": 2},
        {"nombre": "Leyes de Newton", "importancia": 3},
        {"nombre": "Energía", "importancia": 2},
    ],
}


def test_validacion_sin_nombre():
    try:
        ia_mod.redactar_plan({"nombre": "", "temas": CURSO["temas"]})
        assert False, "deberia lanzar EntradaInvalida"
    except ia_mod.EntradaInvalida:
        pass


def test_validacion_sin_temas():
    try:
        ia_mod.redactar_plan({"nombre": "X", "temas": []})
        assert False, "deberia lanzar EntradaInvalida"
    except ia_mod.EntradaInvalida:
        pass


def test_validacion_nombre_demasiado_largo():
    try:
        ia_mod.redactar_plan({"nombre": "x" * 200, "temas": CURSO["temas"]})
        assert False
    except ia_mod.EntradaInvalida:
        pass


def test_plan_bedrock_ok(monkeypatch):
    monkeypatch.setattr(ia_mod, "BEDROCK", BedrockFalso(texto="Tu plan de Física I está listo."))
    r = ia_mod.redactar_plan(CURSO)
    assert r["fuente"] == "bedrock"
    assert "Física I" in r["plan"]


def test_respuesta_vacia_cae_a_respaldo(monkeypatch):
    monkeypatch.setattr(ia_mod, "BEDROCK", BedrockFalso(texto="   "))
    r = ia_mod.redactar_plan(CURSO)
    assert r["fuente"] == "respaldo"
    assert "Física I" in r["plan"]


def test_prompt_incluye_contexto_y_esenciales():
    sistema, usuario = ia_mod._construir_prompt(CURSO)
    assert "Rumbo" in sistema
    assert "SIN CULPA" in sistema
    assert "Física I" in usuario
    assert "Leyes de Newton" in usuario  # tema esencial priorizado
    assert "10" in usuario  # dias


def test_respaldo_menciona_modo_rescate():
    curso = dict(CURSO, ruta={"dias": 2, "modoRescate": True})
    texto = ia_mod._plan_de_respaldo(curso)
    assert "esencial" in texto.lower() or "clave" in texto.lower()
