"""
Comprehensive Feature Testing Script for AgentX
Tests all endpoints and features systematically
"""

import requests
import json
import time

BASE = 'http://127.0.0.1:8080'

def test_endpoint(name, method, url, payload=None, params=None):
    """Helper to test an endpoint"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    try:
        if method == 'GET':
            r = requests.get(url, params=params, timeout=30)
        else:
            r = requests.post(url, json=payload, timeout=30)
        
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"✅ SUCCESS")
            return True, data
        else:
            print(f"❌ FAILED: {r.text[:500]}")
            return False, r.text
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, str(e)


def main():
    results = {}
    
    # Test 0: Backend Health
    success, data = test_endpoint(
        "0. Backend Health Check",
        "GET", f"{BASE}/"
    )
    if success:
        print(f"   Response: {data}")
    results['health'] = success
    
    # Test 1: Run Identifier
    success, data = test_endpoint(
        "1. Run Identifier (Scan for DQ Issues)",
        "POST", f"{BASE}/run-identifier",
        payload={"project": "hackathon-practice-480508", "table": "dev_dataset.customers"}
    )
    if success:
        result = data.get('result', {})
        issues = result.get('results', [])
        print(f"   Issues Found: {len(issues)}")
        if issues:
            print(f"   Sample Issue: {issues[0]}")
    results['run_identifier'] = success
    
    # Test 2: List Rules
    success, data = test_endpoint(
        "2. List Rules",
        "GET", f"{BASE}/list-rules"
    )
    if success:
        rules = data.get('result', {}).get('rules', [])
        print(f"   Total Rules: {len(rules)}")
        if rules:
            print(f"   Sample Rule: {rules[0].get('rule_id')} - {rules[0].get('rule_text', '')[:50]}")
    results['list_rules'] = success
    
    # Test 3: Create Rule (Manual)
    success, data = test_endpoint(
        "3. Create Rule (Manual)",
        "POST", f"{BASE}/create-rule",
        payload={
            "created_by": "test_user",
            "rule_text": "Test rule - Find customers with missing email",
            "sql_snippet": "SELECT CUS_ID FROM `hackathon-practice-480508.dev_dataset.customers` WHERE CUS_EMAIL IS NULL LIMIT 100"
        }
    )
    if success:
        print(f"   Rule ID: {data.get('result', {}).get('rule_id')}")
    results['create_rule'] = success
    
    # Test 4: NL -> SQL Generation
    success, data = test_endpoint(
        "4. NL -> SQL Generation",
        "POST", f"{BASE}/generate-rule-sql",
        payload={
            "project": "hackathon-practice-480508",
            "nl_text": "Find customers without date of birth",
            "created_by": "test@example.com"
        }
    )
    if success:
        result = data.get('result', {})
        print(f"   Generated SQL: {result.get('sql', '')[:100]}...")
        print(f"   Rule ID: {result.get('rule_id')}")
        print(f"   Status: {result.get('approval_status')}")
    results['nl_to_sql'] = success
    
    # Test 5: Pending Rules (HITL)
    success, data = test_endpoint(
        "5. Get Pending Rules (HITL Queue)",
        "GET", f"{BASE}/pending-rules"
    )
    if success:
        pending = data.get('result', {}).get('pending_rules', [])
        print(f"   Pending Rules: {len(pending)}")
    results['pending_rules'] = success
    
    # Test 6: Run Treatment
    success, data = test_endpoint(
        "6. Run Treatment (Get Suggestions)",
        "POST", f"{BASE}/run-treatment",
        payload={"issue": {"CUS_ID": "123", "CUS_DOB": None, "issue_type": "missing_dob"}}
    )
    if success:
        suggestions = data.get('result', {}).get('suggestions', [])
        print(f"   Treatment Suggestions: {len(suggestions)}")
        if suggestions:
            print(f"   Sample: {suggestions[0].get('description', str(suggestions[0]))[:80]}")
    results['run_treatment'] = success
    
    # Test 7: List Issues
    success, data = test_endpoint(
        "7. List Issues",
        "GET", f"{BASE}/list-issues",
        params={"limit": 100}
    )
    if success:
        issues = data.get('result', {}).get('issues', [])
        print(f"   Total Issues: {len(issues)}")
    results['list_issues'] = success
    
    # Test 8: Anomaly Detection
    success, data = test_endpoint(
        "8. Run Anomaly Detection",
        "GET", f"{BASE}/run-anomaly",
        params={"limit": 20}
    )
    if success:
        result = data.get('result', {})
        print(f"   Status: {result.get('status')}")
        print(f"   Anomalies Inserted: {result.get('inserted', 0)}")
    results['anomaly_detection'] = success
    
    # Test 9: Metrics Dashboard
    success, data = test_endpoint(
        "9. Get Metrics",
        "GET", f"{BASE}/metrics"
    )
    if success:
        result = data.get('result', {})
        print(f"   DOB Completeness: {result.get('dob_completeness', 0)*100:.1f}%")
        print(f"   Total Issues: {result.get('total_issues', 0)}")
        print(f"   Missing DOB Count: {result.get('missing_dob_count', 0)}")
    results['metrics'] = success
    
    # Test 10: Audit Trail
    success, data = test_endpoint(
        "10. Get Audit Trail",
        "GET", f"{BASE}/audit-trail",
        params={"limit": 10}
    )
    if success:
        records = data.get('result', {}).get('records', [])
        print(f"   Audit Records: {len(records)}")
    results['audit_trail'] = success
    
    # Test 11: Rule Preview
    success, data = test_endpoint(
        "11. Rule Preview (Run SQL)",
        "POST", f"{BASE}/run-rule-preview",
        payload={"sql": "SELECT customer_id, customer_name, date_of_birth FROM `hackathon-practice-480508.dev_dataset.customers` WHERE date_of_birth IS NULL LIMIT 10"}
    )
    if success:
        result = data.get('result', {})
        print(f"   Rows Matched: {result.get('count', 0)}")
        preview = result.get('preview', [])
        if preview:
            print(f"   Sample Row: {preview[0]}")
    results['rule_preview'] = success
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📊 Pass Rate: {passed/total*100:.1f}%")
    
    print("\nDetailed Results:")
    for test, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {test}")
    
    return results


if __name__ == "__main__":
    main()
