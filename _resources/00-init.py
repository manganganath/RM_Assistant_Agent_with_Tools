# Databricks notebook source
# MAGIC %md 
# MAGIC # init notebook setting up the backend. 
# MAGIC
# MAGIC Do not edit the notebook, it contains import and helpers for the demo
# MAGIC
# MAGIC <!-- Collect usage data (view). Remove it to disable collection or disable tracker during installation. View README for more details.  -->
# MAGIC <img width="1px" src="https://ppxrzfxige.execute-api.us-west-2.amazonaws.com/v1/analytics?category=data-science&org_id=1444828305810485&notebook=%2F_resources%2F00-init&demo_name=llm-tools-functions&event=VIEW&path=%2F_dbdemos%2Fdata-science%2Fllm-tools-functions%2F_resources%2F00-init&version=1">

# COMMAND ----------

# MAGIC %run ../config

# COMMAND ----------

# MAGIC %run ./00-global-setup-v2

# COMMAND ----------

dbutils.widgets.text("reset_all_data", "false", "Reset Data")
reset_all_data = dbutils.widgets.get("reset_all_data") == "true"
DBDemos.setup_schema(catalog, db, reset_all_data, "ut_docs")

# COMMAND ----------

import time

def endpoint_exists(vsc, vs_endpoint_name):
  try:
    return vs_endpoint_name in [e['name'] for e in vsc.list_endpoints().get('endpoints', [])]
  except Exception as e:
    #Temp fix for potential REQUEST_LIMIT_EXCEEDED issue
    if "REQUEST_LIMIT_EXCEEDED" in str(e):
      print("WARN: couldn't get endpoint status due to REQUEST_LIMIT_EXCEEDED error. The demo will consider it exists")
      return True
    else:
      raise e

def wait_for_vs_endpoint_to_be_ready(vsc, vs_endpoint_name):
  for i in range(180):
    try:
      endpoint = vsc.get_endpoint(vs_endpoint_name)
    except Exception as e:
      #Temp fix for potential REQUEST_LIMIT_EXCEEDED issue
      if "REQUEST_LIMIT_EXCEEDED" in str(e):
        print("WARN: couldn't get endpoint status due to REQUEST_LIMIT_EXCEEDED error. Please manually check your endpoint status")
        return
      else:
        raise e
    status = endpoint.get("endpoint_status", endpoint.get("status"))["state"].upper()
    if "ONLINE" in status:
      return endpoint
    elif "PROVISIONING" in status or i <6:
      if i % 20 == 0: 
        print(f"Waiting for endpoint to be ready, this can take a few min... {endpoint}")
      time.sleep(10)
    else:
      raise Exception(f'''Error with the endpoint {vs_endpoint_name}. - this shouldn't happen: {endpoint}.\n Please delete it and re-run the previous cell: vsc.delete_endpoint("{vs_endpoint_name}")''')
  raise Exception(f"Timeout, your endpoint isn't ready yet: {vsc.get_endpoint(vs_endpoint_name)}")

# COMMAND ----------

from databricks.sdk import WorkspaceClient

def get_shared_warehouse(name=None):
    w = WorkspaceClient()
    warehouses = w.warehouses.list()

    # Check for warehouse by exact name (if provided)
    if name:
        for wh in warehouses:
            if wh.name == name:
                return wh

    # Define fallback priorities
    fallback_priorities = [
        lambda wh: wh.name.lower() == "serverless starter warehouse",
        lambda wh: wh.name.lower() == "shared endpoint",
        lambda wh: wh.name.lower() == "dbdemos-shared-endpoint",
        lambda wh: "shared" in wh.name.lower(),
        lambda wh: "dbdemos" in wh.name.lower(),
        lambda wh: wh.num_clusters > 0,
    ]

    # Try each fallback condition in order
    for condition in fallback_priorities:
        for wh in warehouses:
            if condition(wh):
                return wh

    # Raise an exception if no warehouse is found
    raise Exception(
        "Couldn't find any Warehouse to use. Please create one first or pass "
        "a specific name as a parameter to the get_shared_warehouse(name='xxx') function."
    )


def display_tools(tools):
    display(pd.DataFrame([{k: str(v) for k, v in vars(tool).items()} for tool in tools]))

# COMMAND ----------

def index_exists(vsc, endpoint_name, index_full_name):
    try:
        vsc.get_index(endpoint_name, index_full_name).describe()
        return True
    except Exception as e:
        if 'RESOURCE_DOES_NOT_EXIST' not in str(e):
            print(f'Unexpected error describing the index. This could be a permission issue.')
            raise e
    return False
    
def wait_for_index_to_be_ready(vsc, vs_endpoint_name, index_name):
  for i in range(180):
    idx = vsc.get_index(vs_endpoint_name, index_name).describe()
    index_status = idx.get('status', idx.get('index_status', {}))
    status = index_status.get('detailed_state', index_status.get('status', 'UNKNOWN')).upper()
    url = index_status.get('index_url', index_status.get('url', 'UNKNOWN'))
    if "ONLINE" in status:
      return
    if "UNKNOWN" in status:
      print(f"Can't get the status - will assume index is ready {idx} - url: {url}")
      return
    elif "PROVISIONING" in status:
      if i % 40 == 0: print(f"Waiting for index to be ready, this can take a few min... {index_status} - pipeline url:{url}")
      time.sleep(10)
    else:
        raise Exception(f'''Error with the index - this shouldn't happen. DLT pipeline might have been killed.\n Please delete it and re-run the previous cell: vsc.delete_index("{index_name}, {vs_endpoint_name}") \nIndex details: {idx}''')
  raise Exception(f"Timeout, your index isn't ready yet: {vsc.get_index(index_name, vs_endpoint_name)}")

def wait_for_model_serving_endpoint_to_be_ready(ep_name):
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.serving import EndpointStateReady, EndpointStateConfigUpdate
    import time

    # TODO make the endpoint name as a param
    # Wait for it to be ready
    w = WorkspaceClient()
    state = ""
    for i in range(200):
        state = w.serving_endpoints.get(ep_name).state
        if state.config_update == EndpointStateConfigUpdate.IN_PROGRESS:
            if i % 40 == 0:
                print(f"Waiting for endpoint to deploy {ep_name}. Current state: {state}")
            time.sleep(10)
        elif state.ready == EndpointStateReady.READY:
          print('endpoint ready.')
          return
        else:
          break
    raise Exception(f"Couldn't start the endpoint, timeout, please check your endpoint for more details: {state}")
