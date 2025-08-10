# Databricks notebook source
# MAGIC %md ## Install required packages
# MAGIC

# COMMAND ----------

# MAGIC %pip install --upgrade 'mlflow[databricks]>=3.1.0' openai 'databricks-connect==16.4.0' openpyxl
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ./config

# COMMAND ----------

import pandas as pd

# COMMAND ----------

# MAGIC %md ## Load evaluation data

# COMMAND ----------

from pyspark.sql import functions as F

sdf_struct = spark.table(f"{catalog}.{schema}.eval_data").select(
    F.struct(F.col("Question").alias("question")).alias("inputs"),
    F.struct(F.col("Answer").alias("expected_response")).alias("expectations")
)

# Row.asDict(recursive=True) gives you plain Python dicts
eval_data = [row.asDict(recursive=True) for row in sdf_struct.collect()]

# COMMAND ----------

display(eval_data)

# COMMAND ----------

# MAGIC %md ## Step 3. Define evaluation criteria

# COMMAND ----------

from mlflow.genai.scorers import *
import mlflow.genai

# Define evaluation scorers
scorers = [
    RelevanceToQuery(),
    Safety(),
    Guidelines(
        guidelines="Responses must be factually similar, wording may differ.",
        name="Similarity",
    )
]

# COMMAND ----------

# MAGIC %md ## Run evaluation

# COMMAND ----------

import os
import requests
import json
import re
import ast
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

db_token = dbutils.secrets.get(scope="nuwan_hf", key="petco")

url = 'https://dbc-5c83b309-9456.cloud.databricks.com/serving-endpoints/agents_workspace-rm_agent-rm_agent/invocations'
headers = {'Authorization': f'Bearer {db_token}', 'Content-Type': 'application/json'}

@mlflow.trace
def score_agent(question: str):
  ds_dict = {"messages": [{"role": "user", "content": question}]}
  data_json = json.dumps(ds_dict, allow_nan=True)
  response = requests.request(method='POST', headers=headers, url=url, data=data_json)
  if response.status_code != 200:
    raise Exception(f'Request failed with status {response.status_code}, {response.text}')
    return ""
  else:
    outer = json.loads(response.content.decode("utf-8"))
    content =outer["messages"][-1]["content"]
    #print(content)
    return content

# COMMAND ----------

# Run evaluation

results = mlflow.genai.evaluate(
    data=eval_data,
    predict_fn=score_agent,
    scorers=scorers
)

# COMMAND ----------

# MAGIC %md ## Review the results
# MAGIC
# MAGIC You can review the results in the interactive cell output, or in the MLflow Experiment UI. To open the Experiment UI, click the link in the cell results (shown below), or click **Experiments** in the left sidebar.
