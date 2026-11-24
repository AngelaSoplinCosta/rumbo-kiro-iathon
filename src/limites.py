"""
Limites diarios de uso de IA (Bedrock) para evitar costos inesperados.

La API es publica (sin login), asi que el gasto se acota en tres niveles:
  - por curso: cada espacio tiene su cupo de chat, plan y deteccion de temas;
  - por IP de origen: frena a un solo cliente que crea cursos en bucle;
  - global: tope duro de llamadas a Bedrock por dia para toda la cuenta.

Cada contador es un item de DynamoDB `limite#<clave>#<fecha>` que se incrementa
con una escritura condicional atomica (sin carreras entre Lambdas concurrentes).
El atributo `expira` (epoch) deja que el TTL de DynamoDB borre los contadores.
Ademas, API Gateway limita la tasa por segundo (template.yaml, DefaultRouteSettings).
"""

import os
from datetime import datetime, timedelta, timezone

from botocore.exceptions import ClientError

# Peru no tiene horario de verano: UTC-5 fijo. Los cupos se reinician a medianoche de Lima.
ZONA_LIMA = timezone(timedelta(hours=-5))


def _entero_env(nombre, defecto):
    try:
        return int(os.environ.get(nombre, defecto))
    except ValueError:
        return defecto


# Cupos diarios. Se pueden ajustar por variable de entorno sin tocar codigo.
LIMITES = {
    "chat": _entero_env("LIMITE_CHAT_CURSO_DIA", 40),
    "plan": _entero_env("LIMITE_PLAN_CURSO_DIA", 10),
    "temas": _entero_env("LIMITE_TEMAS_CURSO_DIA", 15),
    "ip": _entero_env("LIMITE_IA_IP_DIA", 80),
    "global": _entero_env("LIMITE_IA_GLOBAL_DIA", 1500),
}

MENSAJE_LIMITE = "Llegaste al límite de IA de hoy. Mañana se renueva; mientras tanto puedes seguir con tu ruta."


class LimiteExcedido(Exception):
    """Se agoto un cupo diario (el handler responde 429)."""


def hoy_lima():
    return datetime.now(ZONA_LIMA).date()


def _expira(fecha):
    """Epoch de 2 dias despues de la fecha: margen para que el TTL limpie."""
    limite = datetime(fecha.year, fecha.month, fecha.day, tzinfo=ZONA_LIMA) + timedelta(days=2)
    return int(limite.timestamp())


def _consumir_uno(tabla, clave, maximo, fecha):
    """Suma 1 al contador si no supera `maximo`. Devuelve False si ya estaba lleno."""
    try:
        tabla.update_item(
            Key={"id": f"limite#{clave}#{fecha.isoformat()}"},
            UpdateExpression="SET tipo = :tipo, expira = :expira ADD conteo :uno",
            ConditionExpression="attribute_not_exists(conteo) OR conteo < :maximo",
            ExpressionAttributeValues={
                ":tipo": "limite",
                ":expira": _expira(fecha),
                ":uno": 1,
                ":maximo": maximo,
            },
        )
        return True
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return False
        raise


def consumir(tabla, operacion, curso_id=None, ip=None, fecha=None):
    """Reserva una llamada a Bedrock. Lanza LimiteExcedido si algun cupo esta lleno.

    Se revisa de lo mas especifico a lo mas general. Si un cupo esta lleno, los
    anteriores ya sumaron 1: es un sobreconteo menor y conservador (nunca deja
    pasar de mas).
    """
    fecha = fecha or hoy_lima()
    claves = []
    if curso_id:
        claves.append((f"{operacion}#{curso_id}", LIMITES[operacion]))
    if ip:
        claves.append((f"ip#{ip}", LIMITES["ip"]))
    claves.append(("global", LIMITES["global"]))

    for clave, maximo in claves:
        if not _consumir_uno(tabla, clave, maximo, fecha):
            raise LimiteExcedido(MENSAJE_LIMITE)
