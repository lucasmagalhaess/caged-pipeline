import requests
import json
import os
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient

STORAGE_CONN_STR = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_BRONZE = "bronze"

TIPOS_UNIDADE = {
    "01": "POSTO DE SAUDE",
    "02": "CENTRO DE SAUDE/UNIDADE BASICA",
    "04": "POLICLINICA",
    "05": "HOSPITAL GERAL",
    "06": "HOSPITAL ESPECIALIZADO",
    "07": "HOSPITAL DIA",
    "15": "UNIDADE MISTA",
    "20": "PRONTO SOCORRO GERAL",
    "21": "PRONTO SOCORRO ESPECIALIZADO",
    "22": "CONSULTORIO ISOLADO",
    "36": "CLINICA/CENTRO DE ESPECIALIDADE",
    "39": "UNIDADE DE APOIO DIAGNOSE E TERAPIA",
    "62": "HOSPITAL DIA ISOLADO",
    "70": "CENTRO DE SAUDE MENTAL",
    "77": "SERVICO DE ATENCAO DOMICILIAR ISOLADO",
    "78": "UNIDADE DE ATENCAO EM REGIME RESIDENCIAL",
    "81": "LABORATORIO DE SAUDE PUBLICA",
    "85": "CENTRO DE IMUNIZACAO",
}

def get_estabelecimentos(limit=500, offset=0):
    url = f"https://apidadosabertos.saude.gov.br/cnes/estabelecimentos?limit={limit}&offset={offset}"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json().get("estabelecimentos", [])

def save_to_blob(data, blob_name):
    client = BlobServiceClient.from_connection_string(STORAGE_CONN_STR)
    container = client.get_container_client(CONTAINER_BRONZE)
    container.upload_blob(
        name=blob_name,
        data=json.dumps(data, ensure_ascii=False, indent=2),
        overwrite=True
    )
    print(f"Salvo no Blob Storage: {blob_name}")

def extract():
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")

    print("Extraindo estabelecimentos de saude do CNES...")
    todos = []

    for offset in range(0, 500, 100):
        batch = get_estabelecimentos(limit=100, offset=offset)
        if not batch:
            break
        todos.extend(batch)
        print(f"  Extraidos: {len(todos)} estabelecimentos")

    payload = {
        "extraction_date": today,
        "extraction_timestamp": timestamp,
        "total_estabelecimentos": len(todos),
        "estabelecimentos": todos
    }

    blob_name = f"saude/{today}/estabelecimentos_{timestamp.replace(':', '-')}.json"
    save_to_blob(payload, blob_name)

    print(f"\nTotal extraido: {len(todos)} estabelecimentos")
    return blob_name

if __name__ == "__main__":
    extract()
