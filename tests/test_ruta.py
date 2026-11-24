"""Pruebas del generador de temario y ruta (src/ruta.py)."""

import os
from datetime import date

os.environ.setdefault("TEAM_ID", "T034")
os.environ.setdefault("TABLE_NAME", "tabla-falsa")

import ruta as ruta_mod

TEXTO = """
Capitulo 1: Cinematica
La cinematica estudia el movimiento de los cuerpos sin considerar sus causas.
La velocidad es el cambio de posicion en el tiempo.

Capitulo 2: Leyes de Newton
La segunda ley de Newton establece que F = m por a.
El principio de inercia describe el reposo de los cuerpos.

Capitulo 3: Trabajo y Energia
El trabajo es la fuerza por la distancia recorrida.
"""


def test_detecta_temas_desde_titulos():
    temas = ruta_mod.detectar_temas(TEXTO)
    nombres = " ".join(t["nombre"].lower() for t in temas)
    assert len(temas) >= 3
    assert "cinematica" in nombres
    assert "newton" in nombres


def test_tema_con_ley_es_esencial():
    temas = ruta_mod.detectar_temas(TEXTO)
    newton = [t for t in temas if "newton" in t["nombre"].lower()][0]
    assert newton["importancia"] == 3


def test_ruta_cabe_en_los_dias():
    temas = ruta_mod.detectar_temas(TEXTO)
    hoy = date(2026, 10, 30)
    examen = date(2026, 11, 9)
    r = ruta_mod.generar_ruta(temas, hoy, examen, minutos_por_dia=60)
    assert r["dias"] == 10
    assert len(r["sesiones"]) >= 1
    # Ninguna sesion de estudio supera los minutos del dia.
    for s in r["sesiones"]:
        if s["tipo"] == "estudio":
            assert s["minutos"] <= 60


def test_modo_rescate_cuando_no_alcanza():
    # Muchos temas pesados y pocos dias -> rescate.
    temas = [
        {"orden": i + 1, "nombre": f"Tema {i+1}", "importancia": 2, "minutosEstimados": 60, "requiere": []}
        for i in range(10)
    ]
    temas[0]["importancia"] = 3
    hoy = date(2026, 10, 30)
    examen = date(2026, 11, 1)  # solo 2 dias
    r = ruta_mod.generar_ruta(temas, hoy, examen, minutos_por_dia=60)
    assert r["modoRescate"] is True


# Detector inyectado = heuristica local, para que las pruebas no llamen a Bedrock.
HEUR = ruta_mod.detectar_temas


def test_construir_curso_integra_todo():
    curso = ruta_mod.construir_curso(
        nombre="Física I", documentos=[{"nombre": "cap1.pdf", "texto": TEXTO}],
        fecha_examen_iso="2026-11-09", minutos_por_dia=60, hoy=date(2026, 10, 30),
        detector=HEUR,
    )
    assert curso["nombre"] == "Física I"
    assert len(curso["temas"]) >= 3
    assert curso["ruta"]["sesiones"]
    assert curso["ruta"]["fechaExamen"] == "2026-11-09"
    assert len(curso["documentos"]) == 1


def test_examen_en_el_pasado_se_corrige():
    curso = ruta_mod.construir_curso(
        nombre="X", documentos=[{"nombre": "d.pdf", "texto": TEXTO}],
        fecha_examen_iso="2020-01-01", minutos_por_dia=60, hoy=date(2026, 10, 30),
        detector=HEUR,
    )
    assert curso["ruta"]["dias"] > 0


def test_ruta_solo_usa_documentos_incluidos():
    curso = {
        "nombre": "Física", "fechaExamen": "2026-11-20", "minutosPorDia": 60,
        "documentos": [
            {"id": "1", "texto": "Capitulo 1: Cinematica. La velocidad es el cambio de posicion.", "incluir": True},
            {"id": "2", "texto": "Capitulo 9: Relatividad. La energia es masa por c al cuadrado.", "incluir": False},
        ],
    }
    ruta_mod.regenerar(curso, hoy=date(2026, 10, 30), detector=HEUR)
    nombres = " ".join(t["nombre"].lower() for t in curso["temas"])
    assert "relatividad" not in nombres  # el doc excluido no aporta temas


def test_agregar_documento_suma_temas():
    curso = ruta_mod.construir_curso(
        nombre="Física I", documentos=[{"nombre": "cap1.pdf", "texto": "Capitulo 1: Cinematica. La velocidad es el cambio de posicion."}],
        fecha_examen_iso="2026-11-20", minutos_por_dia=60, hoy=date(2026, 10, 30),
        detector=HEUR,
    )
    temas_antes = len(curso["temas"])
    curso["documentos"].append(ruta_mod.nuevo_documento("cap2.pdf", TEXTO))
    ruta_mod.regenerar(curso, hoy=date(2026, 10, 30), detector=HEUR)
    assert len(curso["documentos"]) == 2
    assert len(curso["temas"]) >= temas_antes


def test_detector_ia_con_respaldo_heuristico(monkeypatch):
    # Si el detector de IA devuelve None, se usa la heuristica y fuente='heuristica'.
    import ia as ia_mod
    monkeypatch.setattr(ia_mod, "detectar_temas_ia", lambda *_a, **_k: None)
    curso = {
        "nombre": "X", "fechaExamen": "2026-11-20", "minutosPorDia": 60,
        "documentos": [{"id": "1", "texto": TEXTO, "incluir": True}],
    }
    ruta_mod.regenerar(curso, hoy=date(2026, 10, 30))
    assert curso["temasFuente"] == "heuristica"
    assert curso["temas"]


def test_detector_ia_usa_bedrock(monkeypatch):
    import ia as ia_mod
    fake = [{"orden": 1, "nombre": "Tema IA", "importancia": 3, "minutosEstimados": 40, "requiere": []}]
    monkeypatch.setattr(ia_mod, "detectar_temas_ia", lambda *_a, **_k: fake)
    curso = {
        "nombre": "X", "fechaExamen": "2026-11-20", "minutosPorDia": 60,
        "documentos": [{"id": "1", "texto": TEXTO, "incluir": True}],
    }
    ruta_mod.regenerar(curso, hoy=date(2026, 10, 30))
    assert curso["temasFuente"] == "bedrock"
    assert curso["temas"][0]["nombre"] == "Tema IA"
