"""
Validacion de entrada de los endpoints de cursos.

El PDF se lee en el navegador (pdf.js) y la API recibe solo el texto extraido,
asi que aqui se valida lo que llega: cantidad de documentos, nombre y extension,
volumen de texto, que el texto sea legible y los campos del curso.

El limite de texto existe porque el curso completo se guarda como un item de
DynamoDB, que admite como maximo 400 KB.
"""

import json
import re
from datetime import date, timedelta

MAX_CUERPO_BYTES = 1_000_000  # 1 MB por solicitud (API Gateway admite 10 MB, Lambda 6 MB)
MAX_DOCUMENTOS = 10  # por curso, contando los ya subidos
MAX_NOMBRE_DOCUMENTO = 150
MAX_NOMBRE_CURSO = 120
MAX_TEXTO_DOCUMENTO = 120_000  # caracteres (~30 paginas de texto denso)
MAX_TEXTO_CURSO = 250_000  # caracteres en total por curso
MAX_ITEM_BYTES = 380_000  # margen bajo el limite de 400 KB de DynamoDB
MIN_TEXTO = 20
MIN_MINUTOS_DIA, MAX_MINUTOS_DIA = 10, 480
MAX_DIAS_AL_EXAMEN = 365
MIN_PROPORCION_LEGIBLE = 0.85

EXTENSIONES = (".pdf",)

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class EntradaInvalida(Exception):
    """La solicitud no es valida. `codigo` es el estado HTTP (400 o 413)."""

    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.codigo = codigo


def leer_cuerpo(event):
    """Parsea el JSON del cuerpo con tope de tamano. Devuelve un dict."""
    crudo = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raise EntradaInvalida("Envía el cuerpo como JSON, no como binario.")
    if len(crudo.encode("utf-8")) > MAX_CUERPO_BYTES:
        raise EntradaInvalida("La solicitud es demasiado grande (máximo 1 MB de texto).", 413)
    try:
        cuerpo = json.loads(crudo)
    except json.JSONDecodeError:
        raise EntradaInvalida("cuerpo JSON invalido")
    if not isinstance(cuerpo, dict):
        raise EntradaInvalida("El cuerpo debe ser un objeto JSON.")
    return cuerpo


def _es_legible(texto):
    """Rechaza binario pegado como texto: exige una proporcion alta de caracteres imprimibles."""
    muestra = texto[:5000]
    if not muestra:
        return False
    imprimibles = sum(1 for c in muestra if c.isprintable() or c in "\n\r\t")
    return imprimibles / len(muestra) >= MIN_PROPORCION_LEGIBLE


def validar_documentos(cuerpo, ya_subidos=0, texto_existente=0):
    """Valida la lista de documentos. Acepta {documentos:[...]} o el formato antiguo {texto}.

    Devuelve [{nombre, texto}] con el texto limpio de caracteres de control.
    """
    docs = cuerpo.get("documentos")
    if docs is None and cuerpo.get("texto") is not None:
        docs = [{"nombre": cuerpo.get("nombreArchivo") or "documento.pdf", "texto": cuerpo["texto"]}]
    if docs is None:
        docs = []
    if not isinstance(docs, list):
        raise EntradaInvalida("'documentos' debe ser una lista.")
    if not docs:
        raise EntradaInvalida("Sube al menos un PDF con texto legible.")
    if ya_subidos + len(docs) > MAX_DOCUMENTOS:
        raise EntradaInvalida(f"Un curso admite como máximo {MAX_DOCUMENTOS} documentos.")

    limpios = []
    total = texto_existente
    for d in docs:
        if not isinstance(d, dict):
            raise EntradaInvalida("Cada documento debe ser un objeto {nombre, texto}.")
        nombre = str(d.get("nombre") or "documento.pdf").strip()
        if len(nombre) > MAX_NOMBRE_DOCUMENTO:
            raise EntradaInvalida("El nombre de un documento es demasiado largo.")
        if not nombre.lower().endswith(EXTENSIONES):
            raise EntradaInvalida(f"'{nombre[:60]}' no es un PDF. Por ahora solo aceptamos archivos .pdf.")
        texto = d.get("texto")
        if not isinstance(texto, str):
            raise EntradaInvalida(f"Falta el texto de '{nombre[:60]}'.")
        if len(texto) > MAX_TEXTO_DOCUMENTO:
            raise EntradaInvalida(
                f"'{nombre[:60]}' es demasiado extenso. Divídelo en partes de unas 30 páginas.", 413
            )
        if texto.strip() and not _es_legible(texto):
            raise EntradaInvalida(f"No pudimos leer el texto de '{nombre[:60]}'. ¿Es un PDF escaneado?")
        texto = _CONTROL.sub("", texto)
        total += len(texto)
        limpios.append({"nombre": nombre, "texto": texto})

    if total > MAX_TEXTO_CURSO:
        raise EntradaInvalida("El curso supera el máximo de texto. Quita algún documento.", 413)
    if len("".join(d["texto"] for d in limpios).strip()) < MIN_TEXTO:
        raise EntradaInvalida("Sube al menos un PDF con texto legible.")
    return limpios


def validar_curso(cuerpo, hoy):
    """Valida nombre, fecha del examen y minutos por dia. Devuelve los valores limpios."""
    nombre = cuerpo.get("nombre")
    if nombre is not None and not isinstance(nombre, str):
        raise EntradaInvalida("'nombre' debe ser texto.")
    nombre = (nombre or "").strip() or "Curso sin nombre"
    if len(nombre) > MAX_NOMBRE_CURSO:
        raise EntradaInvalida("El nombre del curso es demasiado largo.")

    fecha_examen = cuerpo.get("fechaExamen")
    if fecha_examen:  # vacio u omitido: el planificador usa hoy + 10 dias
        try:
            f = date.fromisoformat(str(fecha_examen))
        except ValueError:
            raise EntradaInvalida("'fechaExamen' debe tener formato YYYY-MM-DD.")
        if f <= hoy:
            raise EntradaInvalida("La fecha del examen debe ser posterior a hoy.")
        if f > hoy + timedelta(days=MAX_DIAS_AL_EXAMEN):
            raise EntradaInvalida("La fecha del examen debe estar dentro del próximo año.")
        fecha_examen = f.isoformat()
    else:
        fecha_examen = None

    minutos = cuerpo.get("minutosPorDia", 60)
    if minutos in (None, ""):
        minutos = 60
    if isinstance(minutos, bool):
        raise EntradaInvalida("'minutosPorDia' debe ser un número.")
    try:
        minutos = int(minutos)
    except (TypeError, ValueError):
        raise EntradaInvalida("'minutosPorDia' debe ser un número.")
    if not (MIN_MINUTOS_DIA <= minutos <= MAX_MINUTOS_DIA):
        raise EntradaInvalida(f"'minutosPorDia' debe estar entre {MIN_MINUTOS_DIA} y {MAX_MINUTOS_DIA}.")

    return {"nombre": nombre, "fechaExamen": fecha_examen, "minutosPorDia": minutos}


def validar_tamano_curso(curso):
    """Comprueba que el curso serializado entra en un item de DynamoDB."""
    if len(json.dumps(curso).encode("utf-8")) > MAX_ITEM_BYTES:
        raise EntradaInvalida("El curso es demasiado grande para guardarlo. Quita algún documento.", 413)
