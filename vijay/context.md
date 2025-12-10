Hackathon Context: IP&I Data Quality Management (DQM) Agentic AI

Event: CIO Hackathon - December 10-11, 2025
Theme: "Improving IP&I Data Quality via Agentic AI"
Core Business Goal: Support the migration of 80% of data to GCP by 2025 by automating the clean-up of legacy BaNCS data.

1. The Challenge (The "Ask")

Primary Objective:
Create a centralized Multi-Agent System (MAS) that automates the End-to-End (E2E) Data Quality lifecycle:

Identify issues (using AI & Rules).

Treat issues (Diagnose root cause & strategy).

Remediate issues (Fix in source or escalate).

Measure impact (ROI & Materiality).

Target Data:
Synthetic IP&I BaNCS Life & Pensions data (Valuations Foundation Data Product).

Key Characteristic: Temporal data (Week 1, Week 2, Week 3, Week 4) containing planted anomalies like "Zombie Customers" (Dead -> Alive) and "Ghost Payers" (Deceased but paying premiums).

2. Evaluation Criteria (How We Win)

The judges will score the solution based on four distinct pillars. The Agent's code and architecture must demonstrate these qualities:

🏆 Pillar 1: Innovation & "Standout" Factors

Insightful: Does the system reveal new patterns (e.g., temporal anomalies) rather than just standard null checks?

Actionable: Does it fix the problem or just report it? (Focus on Autonomous Remediation).

Creative: Smart use of GenAI (e.g., Policy-to-SQL, Dynamic Schema Mapping).

⚙️ Pillar 2: Technical Execution (The Agents)

Identifier Agent: Must demonstrate "Rule Synthesis" (creating rules from natural language) and "Dynamic Discovery" (finding columns without hardcoding).

Treatment Agent: Must show "Knowledge Retrieval" (learning from past fixes) and "Strategy Generation" (offering Options A, B, C).

Remediator Agent: Must demonstrate "Safety" (Shadow Validation) and "Velocity" (Time-to-Fix).

Metric Agent: Must translate tech errors into "Business Value" (Cost of Inaction, Regulatory Risk).

🚀 Pillar 3: Route to Live (Feasibility)

Does the architecture integrate with existing infrastructure (GCP, BigQuery, Dataplex)?

Is the design enduring and compliant (Audit trails, Human-in-the-Loop)?

3. Agent-Specific Requirements Checklist

🕵️ Identifier Agent ("The Watchdog")

[ ] Scan: Connect to BigQuery/Dataplex and profile data.

[ ] Synthesize: Generate valid SQL rules from a Natural Language "Policy PDF".

[ ] Learn: Refine rules over time based on feedback.

[ ] Detect: Identify complex anomalies (e.g., Cross-Week Inconsistencies).

🧠 Treatment Agent ("The Strategist")

[ ] Root Cause: Enriched diagnosis (e.g., "System Migration Error" vs "User Entry Error").

[ ] Precedent: Check the Knowledge Bank for previous successful treatments.

[ ] Strategize: If no precedent, use GenAI to propose 3 viable strategies.

[ ] Assign: Route to the correct owner if manual (JIRA integration).

🛠️ Remediator Agent ("The Fixer")

[ ] Auto-Fix: Execute SQL updates directly in the source (for high-confidence issues).

[ ] Integrate: Create JIRA tickets if a system fix is impossible.

[ ] Validate: Run a post-fix "Mini-Scan" (Shadow Validation) to ensure the cure didn't kill the patient.

📊 Metric Agent ("The Analyst")

[ ] Materiality Index: Calculate the severity of the issue (Impact x Volume).

[ ] Cost of Inaction: Estimate the financial risk if the issue is ignored.

[ ] Remediation Velocity: Track the time from Detected -> Fixed.

[ ] Dashboard: Auto-generate a PowerBI/Streamlit view for stakeholders.

4. Key Metrics to Implement

The Metric Agent must calculate and visualize these specific KPIs:

Remediation Velocity: Average time to resolve an issue.

Materiality Index: Financial/Regulatory impact score (High/Med/Low).

Auto-Fix Rate: % of issues resolved without human touch (Target: >80%).

Cost of Inaction: Projected £ risk.

Accuracy: False Positive Rate of the Identifier Agent.

5. The "Hackable Scope" (Focus Areas)

To maximize the score, focus development effort on:

Autonomous Remediation: Moving beyond "detection" to actual "fixing".

Large-Scale Anomaly Detection: specifically the Temporal/Time-Series aspect (Lazarus Protocol).

Governance: The "Human-in-the-Loop" approval workflow (Actionable Emails).