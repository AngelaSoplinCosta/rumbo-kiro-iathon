# CANVAS — Rumbo

## Problema
El abandono del estudio sigue un patron predecible: sobrecarga de material, falta de un plan con fecha, un primer retraso, efecto bola de nieve y, al final, soledad porque nadie nota que la persona dejo de avanzar.

## Propuesta
Rumbo es un companero de estudio que cierra el ciclo completo: toma los documentos del curso y la fecha del examen, arma una ruta diaria basada solo en esos documentos (con citas), acompana cada dia, detecta el riesgo de abandono y ayuda a volver, solo o con amigos.

## Usuarios
Estudiantes universitarios y de institutos en Peru, postulantes a examenes de admision y personas que preparan certificaciones.

## Diferenciadores
1. No es solo un chat con documentos: convierte el material en un plan con fecha limite que se adapta.
2. Detecta el abandono antes de que ocurra y responde de forma gradual y empatica.
3. Consolida el aprendizaje con resumen diario y mapa conceptual semanal.
4. Motivacion en dos capas: progreso personal y competencia social sana.

## Alcance del prototipo (Kiro IAthon)
- Prototipo web estatico y clickeable con la historia de Lucia (datos simulados).
- API serverless de respaldo: `/health` (insignia "API viva") y `/items` sobre DynamoDB (insignia "Persistencia").
- Despliegue en AWS: S3 + CloudFront (prototipo), Lambda + API Gateway + DynamoDB (API).

## Metrica de exito de la demo
Recorrer la historia de Lucia de punta a punta en menos de 7 minutos y mostrar la deteccion de riesgo con la intervencion sin culpa.
