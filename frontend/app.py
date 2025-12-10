import streamlit as st
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import os

# Use local backend by default, can be overridden with environment variable
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8080")


def safe_json_response(resp, default=None):
    """Safely parse JSON response, return default on failure"""
    try:
        if resp.status_code >= 400:
            st.error(f"API Error {resp.status_code}: {resp.text[:500]}")
            return default
        return resp.json()
    except json.JSONDecodeError:
        st.error(f"Invalid JSON response: {resp.text[:500] if resp.text else 'Empty response'}")
        return default
    except Exception as e:
        st.error(f"Error parsing response: {e}")
        return default

# Initialize session state for user
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = "mylilbeast1823@gmail.com"  # Default user
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = "admin"

st.set_page_config(page_title="AgentX - Data Quality Platform", layout="wide", initial_sidebar_state="expanded")

# Sidebar for user info and navigation
with st.sidebar:
    st.title("🤖 AgentX")
    st.caption("AI-Powered Data Quality Platform")
    st.divider()
    
    st.subheader("👤 User Session")
    st.write(f"**Email:** {st.session_state['user_email']}")
    st.write(f"**Role:** {st.session_state['user_role']}")
    
    st.divider()
    st.subheader("📊 Quick Stats")
    try:
        resp = requests.get(f"{BACKEND_URL}/metrics")
        if resp.status_code == 200:
            metrics = resp.json().get("result", {})
            st.metric("DOB Completeness", f"{metrics.get('dob_completeness', 0)*100:.1f}%")
            st.metric("Total Issues", metrics.get('total_issues', 0))
    except:
        st.caption("Stats unavailable")
    
    st.divider()
    st.caption("v2.0 - Enhanced Edition")

st.title("AgentX - Data Quality Agent")
st.caption("Multi-Agent AI System for Data Quality Management")

st.subheader("1. Run Identifier")
# Project is handled by backend config - just show for display
project_display = os.environ.get("AGENTX_PROJECT_DISPLAY", "auto-configured")
table = st.text_input("BigQuery Table", value="dev_dataset.customers")

if st.button("Run Identifier"):
    with st.spinner("Running Identifier Agent..."):
        payload = {"table": table}  # project comes from backend config
        response = requests.post(f"{BACKEND_URL}/run-identifier",
                                 json=payload)
        rj = safe_json_response(response, {})
        result = rj.get("result", {}) if rj else {}
        st.success("Identifier completed")
        st.json(result)
        issues = result.get("results", [])
        st.session_state["issues"] = issues

st.divider()
st.subheader("2. Select Issue for Treatment")

issues = st.session_state.get("issues", [])

if len(issues) > 0:
    selected_issue = st.selectbox(
        "Choose an issue:", issues, format_func=lambda x: f"{x}"
    )

    if st.button("Get Treatment Suggestions"):
        with st.spinner("Running Treatment Agent..."):
            response = requests.post(f"{BACKEND_URL}/run-treatment",
                                     json={"issue": selected_issue})
            rj = safe_json_response(response, {})
            result = rj.get("result") if rj else None
            if result:
                st.success("Treatment suggestions generated")
                st.json(result)
                st.session_state["treatments"] = result.get("suggestions", [])
            else:
                st.error("Failed to get treatment suggestions")

st.divider()
st.subheader("3. Apply Fix")

treatments = st.session_state.get("treatments", [])

if len(treatments) > 0:
    selected_fix = st.selectbox(
        "Choose one fix:", treatments, format_func=lambda x: f"{x['description']}"
    )

    apply_mode = st.selectbox("Apply mode:", ["dryrun", "apply"])

    if st.button("Apply Fix"):
        with st.spinner("Applying fix..."):
            response = requests.post(f"{BACKEND_URL}/apply-fix",
                                     json={"fix": selected_fix, "apply_mode": apply_mode})
            rj = safe_json_response(response, {})
            result = rj.get("result") if rj else None
            if result:
                st.success("Fix processed")
                st.json(result)
            else:
                st.error("Failed to apply fix")

st.divider()
st.subheader("4. Rules — Create / List / Preview")

with st.expander("Create a new rule"):
    created_by = st.text_input("Your name", value="me", key="rule_creator")
    rule_text = st.text_area("Rule description (natural language or SQL)", height=100, key="rule_text")
    sql_snippet = st.text_area("Optional SQL (SELECT...) for preview", height=80, key="rule_sql")

    if st.button("Create Rule"):
        resp = requests.post(f"{BACKEND_URL}/create-rule", json={
            "created_by": created_by, "rule_text": rule_text, "sql_snippet": sql_snippet
        })
        result = safe_json_response(resp, {})
        if result:
            st.json(result)
            st.rerun()

with st.expander("List rules"):
    if st.button("Refresh rules"):
        r = requests.get(f"{BACKEND_URL}/list-rules")
        rj = safe_json_response(r, {})
        st.session_state['rules'] = rj.get("result", {}).get("rules", []) if rj else []

    rules = st.session_state.get("rules", [])
    for rule in rules:
        st.write(f"• **{rule['rule_id']}** — {rule['rule_text']}")
        if rule.get("sql_snippet"):
            if st.button(f"Preview {rule['rule_id']}", key=f"pv_{rule['rule_id']}"):
                resp = requests.post(f"{BACKEND_URL}/run-rule-preview", json={"sql": rule['sql_snippet']})
                result = safe_json_response(resp, {})
                if result:
                    st.json(result)

st.divider()
st.subheader("5. NL → SQL (Auto generate rule with HITL Approval)")

col1, col2 = st.columns([2, 1])

with col1:
    st.write("### Generate Rule from Natural Language")
    nl_text = st.text_area(
        "Describe the data quality check in plain English",
        height=80,
        placeholder="Example: Find customers with missing date of birth\nExample: Find holdings with negative amounts\nExample: Find customers with invalid email addresses",
        key="nl_input"
    )
    
    user_email = st.text_input("Your email", value=st.session_state.get('user_email', 'user@example.com'), key="nl_user_email")
    
    if st.button("🤖 Generate SQL", type="primary"):
        if nl_text:
            with st.spinner("Generating SQL using AI..."):
                resp = requests.post(f"{BACKEND_URL}/generate-rule-sql", json={
                    "project": project,
                    "nl_text": nl_text,
                    "created_by": user_email
                })
                rj = safe_json_response(resp, {})
                if rj and rj.get("result"):
                    result = rj["result"]
                    st.success(f"✅ {result.get('message', 'Rule generated')}")
                    
                    st.write("**Generated SQL:**")
                    st.code(result.get("sql", ""), language="sql")
                    
                    st.info(f"📋 Rule ID: `{result.get('rule_id')}` | Status: **{result.get('approval_status', 'pending').upper()}**")
                    
                    # Store for approval section
                    st.session_state['last_generated_rule'] = result
                else:
                    st.error(f"Generation failed: {rj}")
        else:
            st.warning("Please enter a description")

with col2:
    st.write("### 📖 Tips")
    st.info("""
    **Good descriptions:**
    • "Find missing DOB"
    • "Negative payments"
    • "Invalid emails"
    • "Duplicate customers"
    
    **What happens:**
    1. AI generates SQL
    2. Rule saved as PENDING
    3. Requires approval
    4. Then can be activated
    """)

st.divider()
st.subheader("5B. Rule Approval Queue (HITL)")

tab1, tab2 = st.tabs(["📋 Pending Rules", "✅ Approved Rules"])

with tab1:
    st.write("### Rules Awaiting Approval")
    
    if st.button("🔄 Refresh Pending Rules", key="refresh_pending"):
        resp = requests.get(f"{BACKEND_URL}/pending-rules")
        rj = safe_json_response(resp, {})
        if rj:
            st.session_state['pending_rules'] = rj.get("result", {}).get("pending_rules", [])
    
    pending_rules = st.session_state.get("pending_rules", [])
    
    if pending_rules:
        st.write(f"**{len(pending_rules)} rule(s) pending approval**")
        
        for rule in pending_rules:
            with st.expander(f"🔍 {rule['rule_id']} - {rule['rule_text'][:60]}..."):
                st.write(f"**Created by:** {rule.get('created_by', 'Unknown')}")
                st.write(f"**Created at:** {rule.get('created_ts', 'Unknown')}")
                st.write(f"**Description:** {rule.get('rule_text', 'N/A')}")
                
                st.write("**Generated SQL:**")
                st.code(rule.get('sql_snippet', ''), language="sql")
                
                # Preview option
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👁️ Preview Results", key=f"preview_{rule['rule_id']}"):
                        with st.spinner("Running preview..."):
                            try:
                                preview_resp = requests.post(
                                    f"{BACKEND_URL}/run-rule-preview",
                                    json={"sql": rule['sql_snippet']}
                                )
                                preview_data = safe_json_response(preview_resp, {})
                                if preview_data:
                                    result_data = preview_data.get("result", {})
                                    st.success(f"✅ Preview: {result_data.get('count', 0)} rows matched")
                                    st.dataframe(pd.DataFrame(result_data.get('preview', [])[:10]))
                                else:
                                    st.error("Preview failed")
                            except Exception as e:
                                st.error(f"Preview error: {e}")
                
                with col2:
                    if st.button("✅ Approve", key=f"approve_{rule['rule_id']}", type="primary"):
                        approver = st.session_state.get('user_email', 'user@example.com')
                        approve_resp = requests.post(
                            f"{BACKEND_URL}/approve-rule",
                            json={"rule_id": rule['rule_id'], "approved_by": approver}
                        )
                        if approve_resp.status_code == 200:
                            st.success("✅ Rule approved!")
                            st.balloons()
                            # Refresh pending list
                            st.rerun()
                        else:
                            st.error(f"Approval failed: {approve_resp.text}")
                
                with col3:
                    if st.button("❌ Reject", key=f"reject_{rule['rule_id']}"):
                        reason = st.text_input(
                            "Rejection reason",
                            placeholder="Why are you rejecting this rule?",
                            key=f"reject_reason_{rule['rule_id']}"
                        )
                        if reason:
                            reject_resp = requests.post(
                                f"{BACKEND_URL}/reject-rule",
                                json={
                                    "rule_id": rule['rule_id'],
                                    "rejected_by": st.session_state.get('user_email', 'user@example.com'),
                                    "reason": reason
                                }
                            )
                            if reject_resp.status_code == 200:
                                st.warning("Rule rejected")
                                st.rerun()
                            else:
                                st.error(f"Rejection failed: {reject_resp.text}")
    else:
        st.info("✨ No pending rules. All rules have been reviewed!")

with tab2:
    st.write("### Active (Approved) Rules")
    
    if st.button("🔄 Refresh Active Rules", key="refresh_active"):
        r = requests.get(f"{BACKEND_URL}/list-rules")
        rj = safe_json_response(r, {})
        active_rules = rj.get("result", {}).get("rules", []) if rj else []
        # Filter only active rules
        st.session_state['active_rules'] = [rule for rule in active_rules if rule.get('active', False)]
    
    active_rules = st.session_state.get('active_rules', [])
    
    if active_rules:
        st.write(f"**{len(active_rules)} active rule(s)**")
        
        for rule in active_rules:
            with st.expander(f"✅ {rule['rule_id']} - {rule.get('rule_text', '')[:60]}"):
                st.write(f"**Created by:** {rule.get('created_by', 'Unknown')}")
                st.write(f"**Status:** Active ✅")
                st.code(rule.get('sql_snippet', ''), language="sql")
                
                if st.button(f"▶️ Execute Rule", key=f"exec_{rule['rule_id']}"):
                    with st.spinner("Executing rule..."):
                        exec_resp = requests.post(
                            f"{BACKEND_URL}/run-rule",
                            json={"rule_id": rule['rule_id'], "limit": 200}
                        )
                        rj = safe_json_response(exec_resp, {})
                        if rj:
                            result = rj.get("result", {})
                            st.success(f"✅ Rule executed! {result.get('inserted', 0)} issues detected")
                        else:
                            st.error("Execution failed")
    else:
        st.info("No active rules yet. Approve pending rules to activate them.")

st.divider()
st.subheader("6. Run / Activate Rule")

rules = st.session_state.get("rules", [])
rule_ids = [r["rule_id"] for r in rules]
rule_map = {r["rule_id"]: r for r in rules}

if rule_ids:
    selected_rule_id = st.selectbox("Select rule to run:", options=rule_ids, key="rule_select")
    limit = st.number_input("Limit results to", min_value=10, max_value=2000, value=200, key="rule_limit")

    if st.button("Run selected rule"):
        with st.spinner("Running rule..."):
            resp = requests.post(f"{BACKEND_URL}/run-rule", json={"rule_id": selected_rule_id, "limit": int(limit)})
            rj = safe_json_response(resp, {})
            if rj:
                st.json(rj)
                st.success("Rule run finished. Use 'Issues' view to review.")
            else:
                st.error("Failed to run rule")
else:
    st.info("No rules available. Create or refresh rules first.")

st.divider()
st.subheader("7. Issues (review)")

if st.button("Refresh issues"):
    resp = requests.get(f"{BACKEND_URL}/list-issues?limit=200")
    rj = safe_json_response(resp, {})
    st.session_state['issues_list'] = rj.get("result", {}).get("issues", []) if rj else []

issues_list = st.session_state.get("issues_list", [])
if issues_list:
    for issue in issues_list:
        with st.expander(f"Issue {issue['issue_id']} - Rule: {issue['rule_id']}"):
            st.write(f"**Rule Text:** {issue.get('rule_text', 'N/A')}")
            st.write(f"**Detected:** {issue.get('detected_ts', 'N/A')}")
            st.write(f"**Match Data:**")
            st.json(json.loads(issue['match_json']))

            if st.button(f"Send to Treatment", key=f"treat_{issue['issue_id']}"):
                match_obj = json.loads(issue["match_json"])
                t_resp = requests.post(f"{BACKEND_URL}/run-treatment", json={"issue": match_obj})
                rj = safe_json_response(t_resp, {})
                if rj:
                    st.json(rj)
else:
    st.info("No issues found. Run a rule to detect issues.")

st.divider()
st.subheader("8. Anomaly Detection")

limit = st.number_input("Top N anomalies", min_value=5, max_value=200, value=20, key="anomaly_limit")

if st.button("Run Anomaly Detection"):
    with st.spinner("Detecting anomalies using statistical methods..."):
        resp = requests.get(f"{BACKEND_URL}/run-anomaly", params={"limit": limit})
        rj = safe_json_response(resp, {})
        result = rj.get("result", {}) if rj else {}
        
        if result.get("status") == "success":
            st.success(f"✅ Detected and inserted {result.get('inserted', 0)} anomalies into issues table")
            
            top_anomalies = result.get("top_anomalies", [])
            if top_anomalies:
                st.write(f"**Top {len(top_anomalies)} Anomalies:**")
                for anom in top_anomalies[:5]:  # Show top 5
                    st.write(f"- Customer {anom.get('customer_id')}: Amount ${anom.get('holding_amount'):.2f} (Z-score: {anom.get('z_score', 0):.2f})")
        else:
            st.error("Failed to run anomaly detection")

st.divider()
st.subheader("9. Metrics Dashboard")

if st.button("Refresh Metrics"):
    resp = requests.get(f"{BACKEND_URL}/metrics")
    rj = safe_json_response(resp, {})
    st.session_state['metrics'] = rj.get("result", {}) if rj else {}

metrics = st.session_state.get("metrics", {})
if metrics:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dob_comp = metrics.get("dob_completeness", 0) * 100
        st.metric("DOB Completeness", f"{dob_comp:.1f}%", 
                 delta=f"{metrics.get('missing_dob_count', 0)} missing")
    
    with col2:
        total_issues = metrics.get("total_issues", 0)
        st.metric("Total Issues", total_issues)
    
    with col3:
        total_cust = metrics.get("total_customers", 0)
        st.metric("Total Customers", total_cust)
    
    st.write("### Issues by Rule")
    issues_by_rule = metrics.get("issues_by_rule", [])
    if issues_by_rule:
        for issue in issues_by_rule:
            st.write(f"- **{issue['rule_id']}**: {issue['cnt']} issues ({issue.get('high_severity', 0)} high severity)")
    
    st.write("### Holdings Statistics")
    holdings_stats = metrics.get("holdings_stats", {})
    if holdings_stats:
        st.write(f"- Total Holdings: {holdings_stats.get('total_holdings', 0)}")
        st.write(f"- Average Amount: ${holdings_stats.get('avg_amount', 0):.2f}")
        st.write(f"- Min Amount: ${holdings_stats.get('min_amount', 0):.2f}")
        st.write(f"- Max Amount: ${holdings_stats.get('max_amount', 0):.2f}")
else:
    st.info("Click 'Refresh Metrics' to load data quality metrics")

# ============================================
# NEW ENHANCED FEATURES
# ============================================

st.divider()
st.header("🚀 Enhanced Features")

# Tab layout for organized features
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📜 Rule Versioning",
    "📋 Audit Trail",
    "👥 User Management",
    "📈 Trend Analytics",
    "📥 Export Data"
])

# ============================================
# TAB 1: RULE VERSIONING & ROLLBACK
# ============================================
with tab1:
    st.subheader("📜 Rule Versioning & Rollback")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("### View Rule Versions")
        
        # Get list of rules
        if st.button("Load Rules", key="load_rules_version"):
            resp = requests.get(f"{BACKEND_URL}/list-rules")
            rj = safe_json_response(resp, {})
            if rj:
                st.session_state['all_rules'] = rj.get("result", {}).get("rules", [])
        
        rules = st.session_state.get('all_rules', [])
        if rules:
            rule_ids = [r['rule_id'] for r in rules]
            selected_rule = st.selectbox("Select Rule", rule_ids, key="version_rule_select")
            
            if st.button("View Versions", key="view_versions_btn"):
                resp = requests.get(f"{BACKEND_URL}/rule-versions/{selected_rule}")
                rj = safe_json_response(resp, {})
                if rj:
                    versions = rj.get("result", {}).get("versions", [])
                    st.session_state['rule_versions'] = versions
                    
                    if versions:
                        st.success(f"Found {len(versions)} versions")
                        for v in versions:
                            with st.expander(f"Version {v['version_number']} - {v['created_ts'][:19]}"):
                                st.write(f"**Created by:** {v['created_by']}")
                                st.write(f"**Reason:** {v['change_reason']}")
                                st.write(f"**Active:** {'✅' if v['is_active'] else '❌'}")
                                st.code(v['sql_snippet'], language="sql")
                    else:
                        st.info("No versions found")
    
    with col2:
        st.write("### Rollback Rule")
        
        versions = st.session_state.get('rule_versions', [])
        if versions and len(versions) > 1:
            version_numbers = [v['version_number'] for v in versions]
            target_version = st.selectbox("Rollback to Version", version_numbers[1:], key="rollback_version")
            
            rollback_reason = st.text_input("Reason for rollback", "Reverting to previous version")
            
            if st.button("🔄 Rollback", type="primary", key="rollback_btn"):
                selected_rule = st.session_state.get('version_rule_select')
                if selected_rule:
                    payload = {
                        "rule_id": selected_rule,
                        "target_version": target_version,
                        "rollback_by": st.session_state['user_email']
                    }
                    
                    with st.spinner("Rolling back..."):
                        resp = requests.post(f"{BACKEND_URL}/rollback-rule", json=payload)
                        if resp.status_code == 200:
                            st.success(f"✅ Rule rolled back to version {target_version}")
                            st.balloons()
                        else:
                            st.error(f"❌ Rollback failed: {resp.text}")
        else:
            st.info("Select a rule and view versions to enable rollback")

# ============================================
# TAB 2: AUDIT TRAIL
# ============================================
with tab2:
    st.subheader("📋 Audit Trail")
    st.caption("Track all actions taken in the system")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        action_filter = st.selectbox(
            "Filter by Action Type",
            ["All", "create_rule", "run_rule", "apply_fix", "rollback_rule", "create_user"],
            key="audit_filter"
        )
    
    with col2:
        limit = st.number_input("Records to fetch", min_value=10, max_value=500, value=50, key="audit_limit")
    
    if st.button("🔍 Load Audit Trail", key="load_audit"):
        with st.spinner("Fetching audit records..."):
            params = {"limit": limit}
            if action_filter != "All":
                params["action_type"] = action_filter
            
            resp = requests.get(f"{BACKEND_URL}/audit-trail", params=params)
            rj = safe_json_response(resp, {})
            if rj:
                audit_data = rj.get("result", {}).get("records", [])
                st.session_state['audit_trail'] = audit_data
                st.success(f"Loaded {len(audit_data)} records")
    
    audit_records = st.session_state.get('audit_trail', [])
    if audit_records:
        # Convert to DataFrame for better display
        df = pd.DataFrame(audit_records)
        
        # Display as table
        st.dataframe(
            df[['timestamp', 'user_email', 'action_type', 'action_target', 'status']],
            use_container_width=True,
            hide_index=True
        )
        
        # Detailed view
        st.write("### Detailed View")
        for i, record in enumerate(audit_records[:10]):  # Show top 10 in detail
            with st.expander(f"{record['timestamp'][:19]} - {record['action_type']} by {record['user_email']}"):
                st.json(record)
        
        # Export audit
        if st.button("📥 Export Audit Trail", key="export_audit_btn"):
            st.info("Downloading audit trail...")
            # The export endpoint will handle the download
            st.markdown(f"[Download Audit Trail Excel]({BACKEND_URL}/export/audit)", unsafe_allow_html=True)
    else:
        st.info("Click 'Load Audit Trail' to view activity logs")

# ============================================
# TAB 3: USER MANAGEMENT (RBAC)
# ============================================
with tab3:
    st.subheader("👥 User Management")
    st.caption("Role-Based Access Control")
    
    # Only admins can create users
    if st.session_state['user_role'] == 'admin':
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("### Create New User")
            new_email = st.text_input("Email", key="new_user_email")
            new_name = st.text_input("Full Name", key="new_user_name")
            new_role = st.selectbox("Role", ["business_user", "engineer", "admin"], key="new_user_role")
            
            if st.button("➕ Create User", type="primary", key="create_user_btn"):
                if new_email and new_name:
                    payload = {
                        "email": new_email,
                        "full_name": new_name,
                        "role": new_role
                    }
                    
                    resp = requests.post(f"{BACKEND_URL}/create-user", json=payload)
                    rj = safe_json_response(resp, {})
                    if rj:
                        result = rj.get("result", {})
                        st.success(f"✅ User created: {result.get('user_id')}")
                    else:
                        st.error(f"❌ Failed to create user")
                else:
                    st.warning("Email and name are required")
        
        with col2:
            st.write("### Role Permissions")
            st.info("""
            **Admin**: Full access to all features
            - Create/edit/delete rules
            - Rollback rules
            - Manage users
            - View audit trail
            
            **Engineer**: Technical operations
            - Create/edit rules
            - Run rules
            - Apply fixes
            - View metrics
            
            **Business User**: View & report
            - View issues
            - View metrics
            - Export data
            """)
    else:
        st.warning("⚠️ Admin access required for user management")
        st.info(f"Your role: **{st.session_state['user_role']}**")

# ============================================
# TAB 4: TREND ANALYTICS & VISUALIZATIONS
# ============================================
with tab4:
    st.subheader("📈 Trend Analytics")
    st.caption("Historical metrics and visualizations")
    
    # Save current metrics snapshot
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("💾 Save Metrics Snapshot", key="save_snapshot"):
            with st.spinner("Saving metrics..."):
                resp = requests.post(f"{BACKEND_URL}/save-metrics-snapshot")
                if resp.status_code == 200:
                    st.success("✅ Snapshot saved")
                else:
                    st.error("❌ Failed to save")
    
    with col2:
        st.info("Save periodic snapshots to track metrics over time")
    
    st.divider()
    
    # View trends
    metric_name = st.selectbox(
        "Select Metric to View Trend",
        ["dob_completeness", "total_issues"],
        key="trend_metric"
    )
    
    days = st.slider("Days to show", min_value=1, max_value=30, value=7, key="trend_days")
    
    if st.button("📊 Load Trend", key="load_trend"):
        with st.spinner("Loading trend data..."):
            resp = requests.get(f"{BACKEND_URL}/metrics-trend/{metric_name}", params={"days": days})
            rj = safe_json_response(resp, {})
            if rj:
                trend_data = rj.get("result", {}).get("trend", [])
                st.session_state['trend_data'] = trend_data
    
    trend_data = st.session_state.get('trend_data', [])
    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        df_trend['recorded_ts'] = pd.to_datetime(df_trend['recorded_ts'])
        
        # Create Plotly line chart
        fig = px.line(
            df_trend,
            x='recorded_ts',
            y='metric_value',
            title=f'{metric_name} Trend (Last {days} Days)',
            labels={'recorded_ts': 'Date', 'metric_value': 'Value'},
            markers=True
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Value",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average", f"{df_trend['metric_value'].mean():.4f}")
        with col2:
            st.metric("Min", f"{df_trend['metric_value'].min():.4f}")
        with col3:
            st.metric("Max", f"{df_trend['metric_value'].max():.4f}")
    else:
        st.info("Click 'Load Trend' to view historical data")
    
    # Issues by Rule - Pie Chart
    st.divider()
    st.write("### Issues Distribution by Rule")
    
    if st.button("📊 Load Issues Distribution", key="load_dist"):
        resp = requests.get(f"{BACKEND_URL}/metrics")
        rj = safe_json_response(resp, {})
        if rj:
            metrics = rj.get("result", {})
            issues_by_rule = metrics.get("issues_by_rule", [])
            st.session_state['issues_dist'] = issues_by_rule
    
    issues_dist = st.session_state.get('issues_dist', [])
    if issues_dist:
        df_dist = pd.DataFrame(issues_dist)
        
        fig_pie = px.pie(
            df_dist,
            values='cnt',
            names='rule_id',
            title='Issues by Rule Type',
            hole=0.3
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)

# ============================================
# TAB 5: EXPORT CAPABILITIES
# ============================================
with tab5:
    st.subheader("📥 Export Data")
    st.caption("Download data quality reports for offline analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("### 📄 Issues Report")
        st.info("Export all detected data quality issues")
        
        if st.button("Download Issues (Excel)", key="export_issues", type="primary"):
            st.markdown(f"""
            <a href="{BACKEND_URL}/export/issues" download>
                <button style="
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                ">
                    📥 Download Issues Excel
                </button>
            </a>
            """, unsafe_allow_html=True)
    
    with col2:
        st.write("### 🔧 Remediation Patches")
        st.info("Export all applied fixes and changes")
        
        if st.button("Download Patches (Excel)", key="export_patches", type="primary"):
            st.markdown(f"""
            <a href="{BACKEND_URL}/export/patches" download>
                <button style="
                    background-color: #2196F3;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                ">
                    📥 Download Patches Excel
                </button>
            </a>
            """, unsafe_allow_html=True)
    
    with col3:
        st.write("### 📋 Audit Trail")
        st.info("Export complete audit log for compliance")
        
        if st.button("Download Audit (Excel)", key="export_audit_tab", type="primary"):
            st.markdown(f"""
            <a href="{BACKEND_URL}/export/audit" download>
                <button style="
                    background-color: #FF9800;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                ">
                    📥 Download Audit Excel
                </button>
            </a>
            """, unsafe_allow_html=True)
    
    st.divider()
    st.write("### 📊 Export Options")
    st.write("""
    **Available Export Formats:**
    - Excel (.xlsx) - Full data with multiple sheets
    - Includes summary statistics and charts
    - Compatible with Excel, Google Sheets, and other tools
    
    **Export Contents:**
    - **Issues**: All detected data quality issues with severity, timestamps, and match details
    - **Patches**: Before/after data for all remediations with approval tracking
    - **Audit**: Complete action log with user details and timestamps for compliance
    """)
