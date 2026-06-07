import requests, json
from pyspark.sql.functions import col, when
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

storage_account = "cagedatalake2026"
sas_token = dbutils.secrets.get(scope="licitacoes", key="sas-token-caged")
blob_date = "2026-06-07"
blob_file = "estabelecimentos_2026-06-07T02-32-07.json"
url = "https://" + storage_account + ".blob.core.windows.net/bronze/saude/" + blob_date + "/" + blob_file + "?" + sas_token
response = requests.get(url)
data = response.json()
estabelecimentos = data["estabelecimentos"]

rows = []
for e in estabelecimentos:
    rows.append((
        str(e.get("codigo_cnes", "")),
        str(e.get("nome_razao_social", "")),
        str(e.get("nome_fantasia", "") or ""),
        str(e.get("descricao_esfera_administrativa", "") or ""),
        str(e.get("codigo_tipo_unidade", "") or ""),
        str(e.get("endereco_estabelecimento", "") or ""),
        str(e.get("bairro_estabelecimento", "") or ""),
        float(e.get("latitude_estabelecimento_decimo_grau") or 0),
        float(e.get("longitude_estabelecimento_decimo_grau") or 0),
        str(e.get("descricao_turno_atendimento", "") or ""),
        str(e.get("estabelecimento_faz_atendimento_ambulatorial_sus", "") or ""),
        int(e.get("estabelecimento_possui_centro_cirurgico") or 0),
        int(e.get("estabelecimento_possui_atendimento_hospitalar") or 0),
        int(e.get("estabelecimento_possui_atendimento_ambulatorial") or 0),
        str(e.get("codigo_uf", "") or ""),
        str(data.get("extraction_date", ""))
    ))

schema = StructType([
    StructField("codigo_cnes", StringType()),
    StructField("nome_razao_social", StringType()),
    StructField("nome_fantasia", StringType()),
    StructField("esfera_administrativa", StringType()),
    StructField("codigo_tipo_unidade", StringType()),
    StructField("endereco", StringType()),
    StructField("bairro", StringType()),
    StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType()),
    StructField("turno_atendimento", StringType()),
    StructField("atendimento_sus", StringType()),
    StructField("possui_centro_cirurgico", IntegerType()),
    StructField("possui_atendimento_hospitalar", IntegerType()),
    StructField("possui_atendimento_ambulatorial", IntegerType()),
    StructField("codigo_uf", StringType()),
    StructField("extraction_date", StringType()),
])

df = spark.createDataFrame(rows, schema)

df_silver = df \
    .withColumn("tipo_estabelecimento",
        when(col("possui_atendimento_hospitalar") == 1, "hospital")
        .when(col("possui_centro_cirurgico") == 1, "cirurgico")
        .when(col("possui_atendimento_ambulatorial") == 1, "ambulatorial")
        .otherwise("outros")) \
    .withColumn("atende_sus",
        when(col("atendimento_sus") == "SIM", "sim").otherwise("nao")) \
    .withColumn("regiao",
        when(col("codigo_uf").isin(["11","12","13","14","15","16","17"]), "Norte")
        .when(col("codigo_uf").isin(["21","22","23","24","25","26","27","28","29"]), "Nordeste")
        .when(col("codigo_uf").isin(["31","32","33","35"]), "Sudeste")
        .when(col("codigo_uf").isin(["41","42","43"]), "Sul")
        .otherwise("Centro-Oeste"))

from azure.storage.blob import BlobServiceClient
output_data = [row.asDict() for row in df_silver.collect()]
silver_json = "\n".join([json.dumps(r, ensure_ascii=False) for r in output_data])
storage_key = dbutils.secrets.get(scope="licitacoes", key="storage-key-caged")
full_conn_str = "DefaultEndpointsProtocol=https;AccountName=" + storage_account + ";AccountKey=" + storage_key + ";EndpointSuffix=core.windows.net"
client = BlobServiceClient.from_connection_string(full_conn_str)
client.get_container_client("silver").upload_blob(
    name="saude/" + blob_date + "/estabelecimentos_silver.ndjson",
    data=silver_json.encode("utf-8"),
    overwrite=True
)

df_silver.write \
    .format("sqlserver") \
    .option("host", "licitacoes-sql-server.database.windows.net") \
    .option("port", "1433") \
    .option("database", "licitacoesdb") \
    .option("user", "adminlicitacoes") \
    .option("password", "LicitacoesPipeline2026!") \
    .option("dbtable", "estabelecimentos_saude_gold") \
    .mode("overwrite") \
    .save()

print("Pipeline completo! " + str(len(output_data)) + " estabelecimentos processados")
