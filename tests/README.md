# Pruebas automatizadas

Esta carpeta contiene pruebas del backend y de la lógica de estudio. En una ejecución local con Python 3.12, pytest y boto3 se completaron 91 pruebas del código de la entrega.

Desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pytest boto3
AWS_EC2_METADATA_DISABLED=true python -m pytest -q tests
```

Las pruebas utilizan datos y dependencias simuladas. Sus resultados no verifican servicios AWS reales, la seguridad de producción ni el recorrido completo desde el navegador.
