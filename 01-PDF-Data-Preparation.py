# Databricks notebook source
# MAGIC %md
# MAGIC # Preprocess and Index PDFs with Vector Search

# COMMAND ----------

# MAGIC %md
# MAGIC Use DBR 16.4 ML or above

# COMMAND ----------

# MAGIC %pip install databricks-vectorsearch==0.56
# MAGIC
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ./config

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *

# COMMAND ----------

# DBTITLE 1,Our pdf or docx files are available in our Volume (or DBFS)
# List our raw PDF docs
volume_folder = volume_path = f"/Volumes/{catalog}/{schema}/ut_docs"
display(dbutils.fs.ls(volume_folder))

# COMMAND ----------

# DBTITLE 1,ai_parse_document
df = (
    spark.read.format("binaryFile")
    .load(volume_path)
    .select(col("path"), expr("ai_parse_document(content)").alias("parsed"))
    .withColumn("parsed_json", parse_json(col("parsed").cast("string")))
    .selectExpr(
        "path",
        "parsed_json:document:pages",
        "parsed_json:document:elements",
        "parsed_json:corrupted_data",
        "parsed_json:error_status",
        "parsed_json:metadata",
    )
    .orderBy('path')
)

display(df)

# COMMAND ----------

df = df.withColumn("elements_str", col("elements").cast("string"))

# Define the schema for a single element
element_schema = StructType([
    StructField("id", IntegerType(), nullable=True),
    StructField("type", StringType(), nullable=True),
    StructField("content", StringType(), nullable=True),
    StructField("page_id", IntegerType(), nullable=True)
])

# Parse elements_str into an Array of Structs
df_parsed = df.withColumn(
    "elements_arr",
    from_json(col("elements_str"), ArrayType(element_schema))
)

pdf_text_df = df_parsed.withColumn(
    "pdf_content",
    expr("concat_ws(' ', transform(elements_arr, x -> x.content))")
).drop("elements_str", "elements_arr")

display(pdf_text_df)

# COMMAND ----------

def extract_file_name(path):
    return path.split('/')[-1].replace('.pdf', '')

extract_file_name_udf = udf(extract_file_name, StringType())

pdf_text_df = pdf_text_df.withColumn("ut_id", extract_file_name_udf("path"))

# COMMAND ----------

# DBTITLE 1,Add a summary column
from pyspark.sql.functions import pandas_udf, col
from pyspark.sql.types import StringType
import pandas as pd

@pandas_udf(StringType())
def summarize_text(contents: pd.Series) -> pd.Series:
    import mlflow.deployments
    deploy_client = mlflow.deployments.get_deploy_client("databricks")

    def summarize(content):
        chat_response = deploy_client.predict(
            endpoint="databricks-meta-llama-3-1-8b-instruct",
            inputs={
                "messages": [
                    {
                        "role": "user",
                        "content": f"Summarize the following text as a single paragraph without providing any additional text: {content}"
                    }
                ],
                "temperature": 0.0,
                "max_tokens": 400
            }
        )

        return chat_response['choices'][0]['message']['content'].replace('\n', '').replace("\\'", "'")

    return contents.apply(summarize)

# Add summary column to pdf_text_df
pdf_text_summary_df = pdf_text_df.withColumn("summary", summarize_text(col("pdf_content")))

display(pdf_text_summary_df)

# COMMAND ----------

from pyspark.sql.functions import monotonically_increasing_id, col, concat_ws, lit, when, col

# Add a column with a unique identifier
combined_df = pdf_text_summary_df.withColumn("id", monotonically_increasing_id())

# Step 3: Add an additional column with combined information
processed_df = combined_df.withColumn("combined_info", concat_ws("\n",
    concat_ws(": ", lit("UT ID"), col("ut_id")),
    concat_ws(": ", lit("Summary"), col("summary"))
))

processed_df.write.mode('overwrite').saveAsTable(f"{catalog}.{schema}.ut_pdf_docs")

display(processed_df)

# COMMAND ----------

# DBTITLE 1,Enable Change DataFeed
spark.sql(f"ALTER TABLE {catalog}.{schema}.ut_pdf_docs SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient
import databricks.sdk.service.catalog as c

vsc = VectorSearchClient()

#The table we'd like to index
source_table_fullname = f"{catalog}.{schema}.ut_pdf_docs"
# Where we want to store our index
vs_index_fullname = f"{catalog}.{schema}.ut_pdf_docs_vs_index"

# COMMAND ----------

# DBTITLE 1,Creating the Vector Search endpoint
if not endpoint_exists(vsc, VECTOR_SEARCH_ENDPOINT_NAME):
    vsc.create_endpoint(name=VECTOR_SEARCH_ENDPOINT_NAME, endpoint_type="STANDARD")

wait_for_vs_endpoint_to_be_ready(vsc, VECTOR_SEARCH_ENDPOINT_NAME)
print(f"Endpoint named {VECTOR_SEARCH_ENDPOINT_NAME} is ready.")

# COMMAND ----------

# DBTITLE 1,Create the managed vector search using our endpoint
if not index_exists(vsc, VECTOR_SEARCH_ENDPOINT_NAME, vs_index_fullname):
  print(f"Creating index {vs_index_fullname} on endpoint {VECTOR_SEARCH_ENDPOINT_NAME}...")
  try:
    vsc.create_delta_sync_index(
      endpoint_name=VECTOR_SEARCH_ENDPOINT_NAME,
      index_name=vs_index_fullname,
      source_table_name=source_table_fullname,
      pipeline_type="TRIGGERED",
      primary_key="id",
      embedding_source_column='combined_info', #The column containing our text
      embedding_model_endpoint_name='databricks-gte-large-en' #The embedding endpoint used to create the embeddings
    )
  except Exception as e:
    display_quota_error(e, VECTOR_SEARCH_ENDPOINT_NAME)
    raise e
  #Let's wait for the index to be ready and all our embeddings to be created and indexed
  wait_for_index_to_be_ready(vsc, VECTOR_SEARCH_ENDPOINT_NAME, vs_index_fullname)
else:
  #Trigger a sync to update our vs content with the new data saved in the table
  wait_for_index_to_be_ready(vsc, VECTOR_SEARCH_ENDPOINT_NAME, vs_index_fullname)
  vsc.get_index(VECTOR_SEARCH_ENDPOINT_NAME, vs_index_fullname).sync()

print(f"index {vs_index_fullname} on table {source_table_fullname} is ready")

# COMMAND ----------

question = "Describe Small Cap Growth Fund"

results = vsc.get_index(VECTOR_SEARCH_ENDPOINT_NAME, vs_index_fullname).similarity_search(
  query_text=question,
  columns=["ut_id", "summary"],
  num_results=1)
docs = results.get('result', {}).get('data_array', [])
docs

# COMMAND ----------


