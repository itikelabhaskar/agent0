"""
Test suite for new components: config, security, knowledge bank, identifier
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_config_loading():
    """Test configuration module loads correctly"""
    print("\n🧪 Testing Config Loading...")
    try:
        from backend.config import config
        
        assert config.PROJECT_ID is not None
        assert config.DATASET is not None
        assert config.CUSTOMERS_TABLE is not None
        
        print(f"   ✅ Project: {config.PROJECT_ID}")
        print(f"   ✅ Dataset: {config.DATASET}")
        print(f"   ✅ Tables configured: {len([a for a in dir(config) if '_TABLE' in a])}")
        
        return True
    except Exception as e:
        print(f"   ❌ Config test failed: {e}")
        return False

def test_security_sanitization():
    """Test SQL sanitization functions"""
    print("\n🧪 Testing SQL Sanitization...")
    try:
        from backend.security import sanitize_sql, sanitize_identifier
        
        # Test valid SELECT
        valid_sql = "SELECT * FROM table WHERE id = 1"
        result = sanitize_sql(valid_sql)
        print(f"   ✅ Valid SELECT passes")
        
        # Test injection attempt
        try:
            malicious_sql = "SELECT * FROM table; DROP TABLE users;"
            sanitize_sql(malicious_sql)
            print(f"   ❌ Should have blocked DROP statement")
            return False
        except Exception:
            print(f"   ✅ Blocked DROP statement")
        
        # Test identifier sanitization
        valid_id = "table_name_123"
        sanitize_identifier(valid_id)
        print(f"   ✅ Valid identifier passes")
        
        # Test invalid identifier
        try:
            invalid_id = "table'; DROP TABLE users--"
            sanitize_identifier(invalid_id)
            print(f"   ❌ Should have blocked invalid identifier")
            return False
        except Exception:
            print(f"   ✅ Blocked invalid identifier")
        
        return True
    except Exception as e:
        print(f"   ❌ Security test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_knowledge_bank():
    """Test knowledge bank operations"""
    print("\n🧪 Testing Knowledge Bank...")
    try:
        from backend.knowledge_bank import KnowledgeBank
        import tempfile
        import shutil
        
        # Create temporary KB
        temp_dir = tempfile.mkdtemp()
        kb = KnowledgeBank(base_path=temp_dir)
        
        # Test rule addition
        rule_data = {
            "rule_id": "TEST_001",
            "rule_text": "Test rule",
            "sql_snippet": "SELECT * FROM test",
            "created_by": "test_user"
        }
        
        result = kb.add_rule(rule_data, category="completeness")
        print(f"   ✅ Rule added: {result['rule_id']}")
        
        # Test rule retrieval
        retrieved = kb.get_rule("TEST_001")
        assert retrieved is not None
        print(f"   ✅ Rule retrieved: {retrieved['rule_id']}")
        
        # Test treatment addition
        treatment_data = {
            "treatment_id": "T001",
            "issue_type": "missing_dob",
            "description": "Impute from similar records",
            "confidence": 0.8
        }
        
        kb.add_treatment(treatment_data)
        print(f"   ✅ Treatment added")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
        return True
    except Exception as e:
        print(f"   ❌ Knowledge bank test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_identifier_agent():
    """Test identifier agent (without BigQuery connection)"""
    print("\n🧪 Testing Identifier Agent...")
    try:
        from agent.identifier import IdentifierAgent
        
        agent = IdentifierAgent()
        
        # Check methods exist
        assert hasattr(agent, 'detect_missing_dob')
        assert hasattr(agent, 'detect_invalid_emails')
        assert hasattr(agent, 'detect_duplicates')
        assert hasattr(agent, 'detect_outliers')
        assert hasattr(agent, 'run_all_checks')
        
        print(f"   ✅ Identifier agent initialized")
        print(f"   ✅ All detection methods present")
        
        # Test method count
        detection_methods = [m for m in dir(agent) if m.startswith('detect_')]
        print(f"   ✅ {len(detection_methods)} detection methods available")
        
        return True
    except Exception as e:
        print(f"   ❌ Identifier test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_seed_data_files():
    """Test that seed data was generated correctly"""
    print("\n🧪 Testing Seed Data Files...")
    try:
        import pandas as pd
        
        # Check customers
        customers_df = pd.read_csv('fake_data/customers_sample.csv')
        print(f"   ✅ Customers CSV loaded: {len(customers_df)} rows")
        
        # Check for planted issues
        missing_dob = customers_df['CUS_DOB'].isna().sum()
        print(f"   ✅ Missing DOB issues: {missing_dob}")
        
        # Check holdings
        holdings_df = pd.read_csv('fake_data/holdings_sample.csv')
        print(f"   ✅ Holdings CSV loaded: {len(holdings_df)} rows")
        
        # Check for negative amounts
        negative = (holdings_df['holding_amount'] < 0).sum()
        print(f"   ✅ Negative amount issues: {negative}")
        
        return True
    except Exception as e:
        print(f"   ❌ Seed data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Test that all new modules can be imported"""
    print("\n🧪 Testing Module Imports...")
    modules_to_test = [
        'backend.config',
        'backend.security',
        'backend.knowledge_bank',
        'agent.identifier'
    ]
    
    success = True
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except Exception as e:
            print(f"   ❌ {module}: {e}")
            success = False
    
    return success

def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("🚀 AgentX Component Testing Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config_loading),
        ("SQL Sanitization", test_security_sanitization),
        ("Knowledge Bank", test_knowledge_bank),
        ("Identifier Agent", test_identifier_agent),
        ("Seed Data Files", test_seed_data_files)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {test_name}")
    
    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 60)
    
    return all(results.values())

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

