# Databricks notebook source
# MAGIC %md
# MAGIC # Create Tools as UC Functions

# COMMAND ----------

# MAGIC %run ./config

# COMMAND ----------

spark.sql(f"USE CATALOG {catalog}");
spark.sql(f"USE SCHEMA {schema}");

# COMMAND ----------

# DBTITLE 1,Tool for retrieving details on a give unit trust vector search
# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE FUNCTION unit_trust_vector_search (
# MAGIC   input_query STRING
# MAGIC   COMMENT 'The query string for searching Unit Trust documentation.'
# MAGIC ) RETURNS TABLE (summary STRING, ut_id STRING)
# MAGIC LANGUAGE SQL
# MAGIC COMMENT 'Retrive the information related to the the unit trust indicated in the input query.'
# MAGIC RETURN
# MAGIC   SELECT
# MAGIC     summary, ut_id
# MAGIC   FROM
# MAGIC     VECTOR_SEARCH(
# MAGIC       index => 'workspace.rm_agent.ut_pdf_docs_vs_index',
# MAGIC       query_text => input_query,
# MAGIC       num_results => 1
# MAGIC     );

# COMMAND ----------

# DBTITLE 1,Tool for fetching customer data
# MAGIC %sql
# MAGIC CREATE OR REPLACE FUNCTION lookup_customer_info(
# MAGIC   customer_name STRING COMMENT 'Name of the customer whose info to look up'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC COMMENT 'Returns data about a particular customer given the customer name'
# MAGIC RETURN SELECT CONCAT(
# MAGIC     'Customer ID: ', CustomerID, ', ',
# MAGIC     'Name: ', Name, ', ',
# MAGIC     'Gender: ', Gender, ', ',
# MAGIC     'Date Of Birth: ', DateOfBirth, ', ',
# MAGIC     'Address: ', Address, ', ',
# MAGIC     'City: ', City, ', ',
# MAGIC     'State: ', State, ', ',
# MAGIC     'Zip Code: ', ZipCode, ', ',
# MAGIC     'Risk Rating: ', RiskRating, ', ',
# MAGIC     'Email: ', Email, ', ',
# MAGIC     'Customer Since: ', CustomerSince, ', ',
# MAGIC     'Account Balance: ', AccountBalance
# MAGIC   )
# MAGIC   FROM customer_profile
# MAGIC   WHERE Name = customer_name
# MAGIC   LIMIT 1;
# MAGIC
# MAGIC -- let's test our function:
# MAGIC SELECT lookup_customer_info('Brian Long') as cust__info;

# COMMAND ----------

# DBTITLE 1,Tool for fetching unit trusts
# MAGIC %sql
# MAGIC CREATE OR REPLACE FUNCTION lookup_ut_info(
# MAGIC   risk_rating LONG COMMENT 'Maximum product risk rating'
# MAGIC )
# MAGIC RETURNS TABLE(ProductID STRING,
# MAGIC   ProductName STRING,
# MAGIC   RiskRating LONG,
# MAGIC   Currency STRING,
# MAGIC   TotalAssets DOUBLE
# MAGIC )
# MAGIC COMMENT 'Returns a list of unit trusts below the given risk rating'
# MAGIC LANGUAGE SQL
# MAGIC     RETURN
# MAGIC     SELECT ProductID, ProductName, RiskRating, Currency, TotalAssets from unit_trust
# MAGIC     where RiskRating<= risk_rating ORDER BY RiskRating;
# MAGIC
# MAGIC -- let's test our function:
# MAGIC SELECT * FROM lookup_ut_info(3);

# COMMAND ----------

# DBTITLE 1,Tool for currency conversion
# MAGIC %sql
# MAGIC CREATE OR REPLACE FUNCTION convert_to_usd(base_currency STRING, amount FLOAT)
# MAGIC RETURNS FLOAT
# MAGIC LANGUAGE PYTHON
# MAGIC COMMENT 'Convert given currency amount to USD'
# MAGIC AS
# MAGIC $$
# MAGIC   try:
# MAGIC     import requests as r
# MAGIC     response = r.get(f'http://free.currencyconverterapi.com/api/v5/convert?q={base_currency}_USD&compact=y').json()
# MAGIC     conversion_rate = response[f'{base_currency}_USD']['val']
# MAGIC     return amount * conversion_rate
# MAGIC   except:
# MAGIC     return {
# MAGIC       "USD": amount * 1,
# MAGIC       "EUR": amount * 0.9,
# MAGIC       "GBP": amount * 0.8,
# MAGIC       "AUD": amount * 0.7
# MAGIC     }.get(base_currency, 0.0)
# MAGIC $$;
# MAGIC
# MAGIC -- let's test our function:
# MAGIC SELECT convert_to_usd('GBP', 91793398.72) as gbp_in_usd;

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## Using Databricks Playground to test our functions
# MAGIC
# MAGIC Databricks Playground provides a built-in integration with your functions. It'll analyze which functions are available, and call them to properly answer your question.
# MAGIC
# MAGIC
# MAGIC <img src="https://github.com/databricks-demos/dbdemos-resources/blob/main/images/product/llm-tools-functions/llm-tools-functions-playground.gif?raw=true" style="float: right; margin-left: 10px; margin-bottom: 10px;">
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC - Go to Playgound
# MAGIC - Add a model endpoint with tool-calling capability
# MAGIC - Add all the tools created
# MAGIC - Add the provided system prompt
# MAGIC - Get the code for deploying as the agent
