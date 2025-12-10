1) What lives where — the anatomy of your system
On your laptop (local dev)

Source code (agent skeleton, FastAPI backend, Streamlit UI)

Dockerfile, test harness, fake CSVs

Git repository (GitHub)

Local dev tools (VS Code, Python, Docker for local testing)

In the sandbox (hackathon project) — THIS is the only place the real dataset lives:

BigQuery — real synthetic dataset, cleaned tables, result tables, BQML models

Dataplex — table profiling, data quality rules & metrics (if enabled)

Vertex AI — calling Gemini for summaries / rule generation

ADK runtime — run agent flows (can be in Cloud Shell or as deployed service)

Cloud Run — hosts backend endpoints (agent wrapper, APIs) and optionally the UI

Cloud Storage (GCS) — upload raw CSVs, store exported reports or remediation Excel

Logging / Monitoring — Cloud Logging (audit trails for agent actions)


7) What you must not do

Don’t hardcode project/dataset/table names in code.

Don’t attempt to export sandbox data to outside storage.

Don’t try to use service account keys to connect to the sandbox from your laptop (Cloud Shell is the safe path).

Don’t assume Dataplex or a specific BQML model exists — implement fallbacks (run SQL profiling if no Dataplex).