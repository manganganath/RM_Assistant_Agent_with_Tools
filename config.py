# Databricks notebook source
# MAGIC %md 
# MAGIC ## Configuration file
# MAGIC
# MAGIC Please change your catalog and schema here to run the demo on a different catalog.
# MAGIC
# MAGIC <!-- Collect usage data (view). Remove it to disable collection or disable tracker during installation. View README for more details.  -->
# MAGIC <img width="1px" src="https://ppxrzfxige.execute-api.us-west-2.amazonaws.com/v1/analytics?category=data-science&org_id=1444828305810485&notebook=%2Fconfig&demo_name=llm-tools-functions&event=VIEW&path=%2F_dbdemos%2Fdata-science%2Fllm-tools-functions%2Fconfig&version=1">

# COMMAND ----------

VECTOR_SEARCH_ENDPOINT_NAME="vs_endpoint"
LLM_ENDPOINT_NAME = "databricks-meta-llama-3-3-70b-instruct"

catalog = "workspace"
dbName = db = schema = "rm_agent"
