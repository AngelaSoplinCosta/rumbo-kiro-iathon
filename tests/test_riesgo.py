"""Pruebas del calculo de riesgo de abandono (src/riesgo.py) y la replanificacion.

Son funciones puras: reciben `hoy` por parametro, sin red ni base de datos.
"""
from datetime import date, timedelta

import pytest

import riesgo
import ruta

HOY = date(2026, 11, 1)

TEMAS = [
    {"orden": 1, "nombre": "Cinematica", "importancia": 2, "minutosEstimados": 60, "requiere": []},
    {"orden": 2, "nombre": "Leyes de Newton", "importancia": 3, "minutosEstimados": 60, "requiere": ["Cinematica"]},
    {"orden": 3, "nombre": "Trabajo", "importancia": 2, "minutosEstimados": 60, "requiere": []},
    {"orden": 4, "nombre": "Energia", "importancia": 3, "minutosEstimados": 60, "requiere": []},
    {"orden": 5, "nombre": "Dinamica", "importancia": 3, "minutosEstimados": 60, "requiere": []},
    {"orden": 6, "nombre": "Momento", "importancia": 2, "minutosEstimados": 60, "requiere": []},
    {"orden": 7, "nombre": "Rotacion", "importancia": 1, "minutosEstimados": 60, "requiere": []},
]


def _curso(inicio=HOY, dias_examen=14):
    examen = inicio + timedelta(days=dias_examen)
    return {
        "nombre": "Fisica I",
        "creadoEn": inicio.isoformat(),
        "fechaExamen": examen.isoformat(),
        "minutosPorDia": 60,
        "temas": [dict(t) for t in TEMAS],
        "ruta": ruta.generar_ruta([dict(t) for t in TEMAS], inicio, examen, 60),
    }


def _completar(curso, fecha):
    riesgo.registrar_actividad(curso, {"evento": "sesion_completada", "fechaSesion": fecha.isoformat()}, fecha)


def test_curso_nuevo_tiene_riesgo_bajo():
    ev = riesgo.evaluar(_curso(), HOY)
    assert ev["nivel"] == "bajo"
    assert ev["ritmo"]["texto"] == "Vas a buen ritmo"
    assert ev["intervencion"]["accion"] == "recordatorio"
    assert ev["debeReplanificar"] is False


def test_historia_de_lucia_tres_dias_sin_actividad_sube_a_medio():
    # Estudia el dia 1 y luego pasan 3 dias sin actividad (product.md, paso 6).
    curso = _curso()
    _completar(curso, HOY)
    dia_5 = HOY + timedelta(days=4)
    ev = riesgo.evaluar(curso, dia_5)

    assert ev["senales"]["diasSinActividad"] == 3
    assert ev["senales"]["minutosAtrasados"] == 180
    assert ev["nivel"] == "medio"
    assert ev["intervencion"]["accion"] == "sesion_minima"
    assert ev["intervencion"]["minutos"] == 5
    assert ev["debeReplanificar"] is True


def test_estudiante_al_dia_sigue_en_bajo():
    curso = _curso()
    for i in range(3):
        _completar(curso, HOY + timedelta(days=i))
    ev = riesgo.evaluar(curso, HOY + timedelta(days=3))
    assert ev["nivel"] == "bajo"
    assert ev["senales"]["minutosAtrasados"] == 0


def test_inactividad_y_atraso_cerca_del_examen_es_alto():
    # Sin actividad desde que creo el curso y con el examen en 3 dias.
    curso = _curso(dias_examen=10)
    ev = riesgo.evaluar(curso, HOY + timedelta(days=7))
    assert ev["nivel"] == "alto"
    assert ev["intervencion"]["accion"] == "ajustar_plan"


def test_sesion_abandonada_cerca_del_examen_es_critica():
    curso = _curso(dias_examen=10)
    dia_6 = HOY + timedelta(days=5)
    riesgo.registrar_actividad(curso, {"evento": "sesion_abandonada", "fechaSesion": dia_6.isoformat()}, dia_6)
    ev = riesgo.evaluar(curso, HOY + timedelta(days=7))
    assert ev["nivel"] == "critico"
    assert ev["intervencion"]["accion"] == "hablar_meta"
    assert "cambiar_fecha" in ev["intervencion"]["opciones"]


def test_caida_de_aciertos_suma_al_puntaje():
    senales = {
        "diasSinActividad": 0, "minutosAtrasados": 0, "minutosSiguientes3Dias": 180,
        "aciertosPrevios": 0.9, "aciertosUltimos3Dias": 0.6,
        "sesionesAbandonadas7Dias": 0, "sesionesIniciadas7Dias": 2,
        "minutosPendientes": 0, "capacidadRestante": 600, "diasAlExamen": 10,
    }
    r = riesgo.calcular_riesgo(senales)
    caida = next(f for f in r["factores"] if f["nombre"] == "caida_aciertos")
    assert caida["valor"] == 1.0
    assert r["puntaje"] == 15


def test_caida_de_aciertos_exige_minimo_de_respuestas():
    curso = _curso()
    riesgo.registrar_actividad(curso, {"evento": "respuestas", "total": 10, "aciertos": 9}, HOY)
    # Solo 3 respuestas recientes: no alcanza para medir la caida.
    riesgo.registrar_actividad(curso, {"evento": "respuestas", "total": 3, "aciertos": 0}, HOY + timedelta(days=4))
    senales = riesgo.extraer_senales(curso, HOY + timedelta(days=4))
    assert senales["aciertosUltimos3Dias"] is None


def test_respuestas_suficientes_cuentan_como_dia_activo():
    curso = _curso()
    riesgo.registrar_actividad(curso, {"evento": "respuestas", "total": 5, "aciertos": 4}, HOY + timedelta(days=3))
    senales = riesgo.extraer_senales(curso, HOY + timedelta(days=4))
    assert senales["diasSinActividad"] == 0


def test_sesiones_abandonadas_suben_el_factor():
    curso = _curso()
    riesgo.registrar_actividad(curso, {"evento": "sesion_abandonada", "fechaSesion": HOY.isoformat()}, HOY)
    senales = riesgo.extraer_senales(curso, HOY)
    assert senales["sesionesAbandonadas7Dias"] == 1
    assert senales["sesionesIniciadas7Dias"] == 1


def test_misma_intervencion_no_se_repite_dos_dias_seguidos():
    curso = _curso()
    _completar(curso, HOY)
    dia_5 = HOY + timedelta(days=4)
    primera = riesgo.evaluar(curso, dia_5)
    riesgo.guardar_evaluacion(curso, primera)
    segunda = riesgo.evaluar(curso, dia_5 + timedelta(days=1))
    if segunda["nivel"] == primera["nivel"]:
        assert segunda["intervencion"].get("repetida") is True
        assert segunda["debeReplanificar"] is False


def test_mensajes_sin_culpa():
    for nivel in ("bajo", "medio", "alto", "critico"):
        msg = riesgo.elegir_intervencion(nivel, _curso(), HOY)["mensaje"].lower()
        assert "sin estudiar" not in msg
        assert "no has" not in msg


def test_registrar_actividad_valida_entrada():
    curso = _curso()
    with pytest.raises(riesgo.ActividadInvalida):
        riesgo.registrar_actividad(curso, {"evento": "otro"}, HOY)
    with pytest.raises(riesgo.ActividadInvalida):
        riesgo.registrar_actividad(curso, {"evento": "respuestas", "total": 3, "aciertos": 5}, HOY)
    with pytest.raises(riesgo.ActividadInvalida):
        riesgo.registrar_actividad(curso, {"evento": "sesion_completada", "fechaSesion": "2000-01-01"}, HOY)


def test_replanificar_no_acumula_y_conserva_lo_hecho():
    curso = _curso()
    _completar(curso, HOY)
    dia_5 = HOY + timedelta(days=4)
    aviso = ruta.replanificar(curso, dia_5)

    sesiones = curso["ruta"]["sesiones"]
    hechas = [s for s in sesiones if s.get("estado") == "completada"]
    futuras = [s for s in sesiones if s.get("estado") != "completada"]
    assert [s["fecha"] for s in hechas] == [HOY.isoformat()]
    assert all(date.fromisoformat(s["fecha"]) >= dia_5 for s in futuras)
    assert all(s["minutos"] <= 60 for s in futuras if s["tipo"] == "estudio") or curso["ruta"]["modoRescate"]
    # El tema ya estudiado no vuelve a planificarse.
    temas_futuros = {t for s in futuras for t in s["temas"]}
    assert "Cinematica" not in temas_futuros
    assert curso["ruta"]["version"] == 2
    assert aviso.startswith("Reorganizamos tu ruta")


def test_replanificar_activa_modo_rescate_si_no_alcanza():
    curso = _curso(dias_examen=10)
    aviso = ruta.replanificar(curso, HOY + timedelta(days=7))
    assert curso["ruta"]["modoRescate"] is True
    assert "esencial" in aviso
