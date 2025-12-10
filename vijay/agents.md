Sentinel DQM: Enterprise Agent Swarm Architecture

Framework: Google Agent Development Kit (ADK) & Vertex AI Agent Engine Model: Gemini 1.5 Pro / Gemini 3 (Preview) for High-Reasoning Tasks Deployment: Google Cloud Run (Serverless) Frontend: Streamlit Enterprise

1. System Overview

Sentinel DQM is an autonomous multi-agent system designed to clean enterprise data. It leverages a "Swarm Intelligence" pattern where specialized agents collaborate to Detect, Diagnose, Fix, and Report data quality issues.

🌟 Standout Innovations (The "Wow" Factor)

"The Lazarus Protocol" (Temporal Anomaly Detection): Unlike standard tools that check one row at a time, the system compares Week_X vs Week_Y snapshots. It detects if a customer marked DEC (Deceased) in Week 1 suddenly becomes ALV (Alive) in Week 2, or if a Deceased customer continues paying premiums (POLI_GROSS_PMT > 0).

"Dynamic Schema Mapping" (No Hardcoded Columns): The system does NOT rely on exact column names like CUS_LIFE_STATUS. The IdentifierAgent inspects column headers + sample values to infer business meaning (e.g., finding the "Death Date" column whether it's named CUS_DEATH_DATE, D_DATE, or DT_OF_PASSING).

"Policy-to-Code" Engine: The system reads raw PDF policies (e.g., "2025 GDPR Standards") and auto-compiles them into Executable SQL Rules using Gemini 1.5 Pro.

Shadow Validation Sandbox: No fix is ever applied to Production blindly. The Remediator agent spins up a temporary "Shadow Table," applies the fix, runs regression tests, and only then commits.

Actionable Email Governance: Emails sent to Data Stewards contain embedded [APPROVE] and [REJECT] buttons that trigger API callbacks to execute fixes immediately.

2. Environment Setup & Prerequisites

Step 1: Google Cloud Environment

Ensure the following APIs are enabled:

aiplatform.googleapis.com (Vertex AI)

bigquery.googleapis.com

dataplex.googleapis.com

Step 2: Local Development Setup

# 1. Create a fresh Conda environment
conda create -n sentinel_adk python=3.10 -y
conda activate sentinel_adk

# 2. Install dependencies
pip install -r requirements.txt

# 3. Authenticate
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID


3. The Data Protocol (Inter-Agent Communication)

Agents communicate via a strict JSON schema. The DQ_Issue object is the "token" passed around the swarm.

{
  "issue_id": "UUID-Lazarus-001",
  "status": "DETECTED",
  "data_context": {
    "table": "bancs_data.week_4",
    "customer_id": "CUS-7047",
    "semantic_map": {
        "life_status_col": "CUS_LIFE_STATUS",
        "death_date_col": "CUS_DEATH_DATE",
        "payment_col": "POLI_GROSS_PMT"
    },
    "anomaly_type": "LIFE_STATUS_REVERSAL"
  },
  "diagnosis": {
    "rule_violated": "Life Status cannot transition from DEC to ALV",
    "evidence": "Week 3 Status: DEC (Death Date: 2022-04-30) -> Week 4 Status: Active",
    "confidence": 0.99
  },
  "remediation": {
    "strategy_id": "INVESTIGATE_FRAUD",
    "action": "FREEZE_ACCOUNT_AND_ALERT",
    "priority": "CRITICAL"
  }
}


4. Agent Definitions (ADK Specification)

🕵️ Agent A: The Identifier (IdentifierAgent)

Role: The Watchdog. Trigger: New File Upload (Week_4.csv) or Scheduled Cron. System Prompt: "You are an expert Data Auditor using Gemini 3 reasoning. First, map the unknown schema to known Business Concepts. Then, detect temporal inconsistencies."

Tools:

tool_infer_schema(dataset_sample):

Logic: Passes the first 5 rows of the dataset to Gemini 3.

Prompt: "Identify which column represents 'Customer ID', 'Life Status' (Alive/Dead), 'Death Date', and 'Premium Amount'. Return a JSON mapping."

Output: {"life_status": "CUS_LIFE_STATUS", "death_date": "CUS_DEATH_DATE"}.

tool_temporal_scan(current_dataset, previous_dataset, schema_map):

Logic: Performs a JOIN on the inferred Customer ID column.

Checks (using inferred columns):

Lazarus Check: Prev[life_status] == 'DEC' AND Curr[life_status] == 'ALV'.

Ghost Payer Check: Curr[life_status] == 'DEC' AND Curr[payment] > 0.

Date Drift: Curr[death_date] != Prev[death_date].

tool_dataplex_scan(dataset_id):

Logic: Standard static checks (Nulls, Formats, Range checks).

🧠 Agent B: The Treatment (TreatmentAgent)

Role: The Strategist. Trigger: Receives DQ_Issue list. System Prompt: "You are a Forensic Data Analyst. For 'Lazarus' events, assume potential fraud or system error. Prioritize human intervention."

Tools:

tool_strategy_generator(issue_context):

Logic: Uses Gemini 3 Pro to draft options.

Example for Lazarus:

Option A: Revert Status to DEC (System Error).

Option B: Create High-Priority Fraud Case (JIRA).

Option C: Request Proof of Life (Email to Agent).

tool_knowledge_retrieval(error_embedding):

Logic: Checks if this specific Customer ID has a history of status flipping.

🛠️ Agent C: The Remediator (RemediatorAgent)

Role: The Fixer. Trigger: User Approval.

Tools:

tool_shadow_validator(sql_script, row_ids):

Logic: Simulates the fix on a temporary table to ensure no data loss.

tool_jira_manager(action, payload):

Logic: For complex "Lazarus" cases, creates a JIRA ticket assigned to the Fraud Dept.

📊 Agent D: The Metric (MetricAgent)

Role: The Reporter. Trigger: Post-Analysis.

Tools:

tool_report_generator(issues_list):

Logic: Generates a PDF showing "Trend of Death Date Inconsistencies".

tool_email_dispatcher:

Logic: Sends "Monday Morning Briefing" with buttons to Approve fixes.

5. User Interface (Streamlit Enterprise)

Page 1: Temporal Analysis

Selector: Compare [Week 3] vs [Week 4].

Visual: "Sankey Diagram" showing flow of Customers from ALV -> DEC (and the forbidden DEC -> ALV).

Page 2: The Action Board

Red Alert Section: "5 Customers came back to life." (Requires immediate click).

Yellow Warning Section: "12 Customers have shifting Death Dates."

6. Execution Flow (The "Dynamic Zombie" Scenario)

Ingest: System loads Week_3.csv and Week_4.csv.

Map: IdentifierAgent looks at Week 4 headers.

Gemini Reasoning: "Column CUS_LIFE_STATUS contains 'ALV'/'DEC'. This maps to BusinessConcept: LifeStatus."

Gemini Reasoning: "Column CUS_DEATH_DATE contains dates. This maps to BusinessConcept: DeathDate."

Scan: Agent runs tool_temporal_scan using the mapped columns.

Detect: Finds Customer Hannah Beesley.

Week 3: DEC (Death Date: 2022-04-30).

Week 4: Active.

Diagnose: TreatmentAgent flags as CRITICAL: LIFE_STATUS_REVERSAL.

Action: User clicks "Create Ticket" in UI.

Result: JIRA-1024 created: "Investigate Hannah Beesley - Potential System Glitch or Fraud".