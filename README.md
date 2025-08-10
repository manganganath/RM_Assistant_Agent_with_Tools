# RM Assistant Agent with Tools

AI agent for Relationship Managers (RMs) built on the Databricks Data Intelligence Platform. This assistant speeds up relationship managers’ daily workflow by turning unstructured product collateral and governed bank data into actionable answers. It can pull a customer’s profile from governed sources, recommend suitable unit trusts (UTs), compare shortlists across risk/fees/performance, and draft a concise summary the RM can share with the customer, all while calling audited, permissioned tools you define in Unity Catalog.

---

## 📦 Repository Structure

```
.
├── _data/                              # Sample PDFs/CSVs to ingest
├── Streamlit-Chatbot-App/              # Streamlit UI (Databricks App)
├── 00-Import-Source-Data.py            # Import source files to Unity Catalog
├── 01-PDF-Data-Preparation.py          # (Optional) PDF extract/chunk/embed for retrieval
├── 02-Tools-as-UC-Functions.py         # Create tools as Unity Catalog Functions
├── 03-Deploy-Agent-Auto-Generated.py   # Auto-generated agent driver/deployment code
├── 04-Evaluate-Agent.py                # Evaluate the agent
├── agent.py                            # Agent driver (code-first orchestration)
├── config.py                           # Central configuration
└── system_prompt                       # System prompt used by the agent
```

---

## End-to-end Flow

1) **Import files to Unity Catalog**  
2) **Create tools**  
3) **Test agent in Playground**  
4) **Generate agent driver code from Playground**  
5) **Deploy agent using the auto‑generated code from the previous step**  
6) **Evaluate agent**  
7) **Deploy as Databricks App (using Streamlit)**  

---

## 🏗 Architecture Overview

At the core of the system is the **Orchestrator Agent**, powered by the **Llama-3.3-70B-Instruct** model.  
It interprets RM queries, decides which tools to call, orchestrates their execution, and synthesizes the final response.

---

### Components

1. **Orchestrator Agent**  
   - **Role:** Receives a natural language query from the RM (via Playground, API, or Streamlit app).  
   - **Processing:** Uses the Llama-3.3-70B-Instruct model to parse intent, select tools, and chain multiple tool calls if required.  
   - **Governance:** Bound by the `system_prompt`, ensuring scope, compliance, and safe tool usage.

2. **Tools (Unity Catalog Functions)** — all governed and permissioned through Unity Catalog:  
   - **`unit_trust_vector_search`** – Searches vector-indexed UT documents for relevant content.  
   - **`lookup_customer_info`** – Fetches customer profile data from governed UC tables.  
   - **`lookup_ut_info`** – Retrieves detailed information for a given unit trust (NAV, risk rating, etc.).  
   - **`convert_to_usd`** – Converts monetary amounts from any supported currency into USD.

3. **Model: Llama-3.3-70B-Instruct**  
   - Provides natural language understanding, tool selection, and reasoning.  
   - Integrates structured outputs from tools into a coherent final answer for the RM.

4. **Data Layer**  
   - **Delta Tables / UC Volumes** store customer data, UT metadata, and chunked document embeddings.  
   - **Vector Store** for fast semantic search of UT documents.

5. **Interface Layer**  
   - **Databricks AI Playground** for prototyping and debugging the agent.  
   - **Serving Endpoint** for deployed agent access.  
   - **Streamlit App** for an RM-friendly chat UI inside the Databricks App framework.

---

### Flow

1. RM submits a query → Orchestrator Agent receives it.  
2. **Llama-3.3-70B-Instruct** interprets the request and selects one or more tools.  
3. Selected UC functions execute and return structured data.  
4. The model integrates outputs, applies reasoning, and formats the final answer.  
5. Response is returned to the RM via Playground, API, or Streamlit interface.

---

**Diagram:**
![Agent-Tools Relationship](https://github.com/manganganath/RM_Assistant_Agent_with_Tools/blob/main/_image/architecture.png?raw=true)

---

## ✅ Prerequisites

- Access to a **Databricks workspace** with **Unity Catalog** and **Serverless** enabled.  
- Permissions to create UC Functions, Volumes, and Tables.  
- Secrets/credentials for any external systems your tools call.  
- (Optional) Embedding/vector search if using PDF/RAG.

---

## 🚀 Quickstart

### 1) Import files to Unity Catalog
Run **`00-Import-Source-Data.py`** to:
- Select/create your **catalog** and **schema** (edit in `config.py`).
- Upload content from `_data/` into **UC Volumes** and/or ingest CSVs into **Delta tables**.

### 2) Create tools
Run **`02-Tools-as-UC-Functions.py`** to register **Unity Catalog Functions** used as tools by the agent.  
> **Do not rename these tools.** Keep the function names and parameters exactly as defined in this file.

### 3) Test agent in Playground
- In **AI Playground**, create a tool‑calling agent and attach the tools you defined above.  
- Use the `system_prompt` file for the agent’s behavior and guardrails.  
- Chat through representative RM workflows.

### 4) Generate agent driver code from Playground
- From Playground, **Export to code**.  
- Save/commit the exported code (this repo includes `03-Deploy-Agent-Auto-Generated.py`).

### 5) Deploy agent using auto‑generated code
Run **`03-Deploy-Agent-Auto-Generated.py`** to:
- Create/update the agent with the Playground‑validated config (prompt, tools, model, parameters).  
- Deploy as a **Serving** endpoint. Note the endpoint name/URL.

### 6) Evaluate agent
Run **`04-Evaluate-Agent.py`** to:
- Load the evaluation dataset (questions typical of RM workflows).  
- Execute **Mosaic AI Agent Evaluation** to measure quality, cost, and latency.

### 7) Deploy as Databricks App (Streamlit)
- Open **`Streamlit-Chatbot-App/`** and configure environment (e.g., `AGENT_ENDPOINT`, `DATABRICKS_HOST`, `DATABRICKS_TOKEN` if needed).  
- Deploy as a **Databricks App** and share with permitted users/groups.  

---

## ⚙️ Configuration (`config.py`)

Set your catalog/schema, volume/table names, model/endpoint, and any feature flags here.  
Keep these consistent across notebooks, tools, and the app.

---

## 🧪 Evaluation data (example format)

```csv
question,expected_elements
"Show profile for John Tan",["customer_profile"]
"Recommend suitable UTs for John Tan",["ut_reco"]
"Compare ABC Asia Equity vs XYZ Global Bond",["compare","risk","fees","ytd"]
"Summarize findings to inform customer next steps",["summary"]
```

Point `04-Evaluate-Agent.py` to your dataset (CSV/Delta).

---

## 🔐 Security & Governance

- Tools (UC Functions) are controlled with Unity Catalog permissions.  
- Keep PII out of prompts/logs when possible; mask where needed.  
- Include compliance disclaimers and escalation guidance in `system_prompt`.

---

## 🛠 Troubleshooting

- **Tool not invoked** → Ensure it’s attached to the agent and the signature matches what the agent expects.  
- **Permission denied** → Grant `USAGE` on catalog/schema and `EXECUTE` on functions to the caller or service principal.  
- **Playground works, code doesn’t** → Re‑export after changes; redeploy `03-Deploy-Agent-Auto-Generated.py`.  

---

## 📄 License

Apache-2.0 — see `LICENSE`.
