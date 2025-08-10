# Databricks notebook source
# MAGIC %md
# MAGIC # Import Source Data

# COMMAND ----------

# MAGIC %run ./config

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create tables from csv files

# COMMAND ----------

# DBTITLE 1,Create customer_profile table
import pandas as pd

df_customers = spark.createDataFrame(pd.read_csv("_data/customer_profile.csv"))

df_customers.write.format("delta") \
  .mode("overwrite") \
  .option("overwriteSchema", "true") \
  .saveAsTable(f"{catalog}.{schema}.customer_profile")

# COMMAND ----------

# DBTITLE 1,Create unit_trust table
df_ut = spark.createDataFrame(pd.read_csv("_data/unit_trust_info.csv"))

df_ut.write.format("delta") \
  .mode("overwrite") \
  .option("overwriteSchema", "true") \
  .saveAsTable(f"{catalog}.{schema}.unit_trust")

# COMMAND ----------

# DBTITLE 1,Create eval_data table
df_eval = spark.createDataFrame(pd.read_csv("_data/eval_data.csv"))

df_eval.write.format("delta") \
  .mode("overwrite") \
  .option("overwriteSchema", "true") \
  .saveAsTable(f"{catalog}.{schema}.eval_data")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Copy Fund Fact Sheets to a Volume

# COMMAND ----------

# DBTITLE 1,Create a Volume
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.ut_docs")

# COMMAND ----------

# DBTITLE 1,Copy PDFs to Volume
import shutil
import os

volume_folder = f"/Volumes/{catalog}/{schema}/ut_docs"
source_folder = "_data/unit_trust_pdf"

pdf_files = [f for f in os.listdir(source_folder) if f.endswith('.pdf')]

for pdf_file in pdf_files:
    shutil.copy(os.path.join(source_folder, pdf_file), volume_folder)
