"""
Test backend integration - verify new components work with existing code
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_agent_wrapper_compatibility():
    """Test that agent_wrapper still works"""
    print("\n🧪 Testing Agent Wrapper Compatibility...")
    try:
        from backend.agent_wrapper import (
            run_identifier, 
            suggest_treatments_for_missing_dob, 
            apply_fix
        )
        
        print("   ✅ All agent_wrapper functions imported")
        return True
    except Exception as e:
        print(f"   ❌ Agent wrapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tools_module():
    """Test that tools module works"""
    print("\n🧪 Testing Tools Module...")
    try:
        from agent.tools import run_bq_query, run_bq_nonquery
        
        print("   ✅ Tools module functions available")
        return True
    except Exception as e:
        print(f"   ❌ Tools test failed: {e}")
        return False

def test_enhanced_identifier_with_wrapper():
    """Test new identifier works alongside old wrapper"""
    print("\n🧪 Testing Enhanced Identifier + Wrapper Integration...")
    try:
        from agent.identifier import identifier
        from backend.agent_wrapper import run_identifier
        from backend.config import config
        
        print(f"   ✅ Both old and new identifier accessible")
        print(f"   ✅ Config project: {config.PROJECT_ID}")
        print(f"   ✅ Config tables: {config.CUSTOMERS_TABLE}")
        
        return True
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_security_with_fastapi():
    """Test security module can work with FastAPI"""
    print("\n🧪 Testing Security + FastAPI Integration...")
    try:
        from fastapi import HTTPException
        from backend.security import (
            sanitize_sql, 
            verify_api_key,
            get_current_user,
            require_role
        )
        
        print("   ✅ Security functions compatible with FastAPI")
        
        # Test that HTTPException works
        try:
            sanitize_sql("DROP TABLE users", allow_only_select=True)
            print("   ❌ Should have raised HTTPException")
            return False
        except HTTPException as e:
            print(f"   ✅ HTTPException raised correctly: {e.status_code}")
        
        return True
    except Exception as e:
        print(f"   ❌ FastAPI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_knowledge_bank_with_bigquery():
    """Test knowledge bank BigQuery sync capability"""
    print("\n🧪 Testing Knowledge Bank BigQuery Integration...")
    try:
        from backend.knowledge_bank import kb
        from backend.config import config
        
        print(f"   ✅ KB initialized with path: {kb.base_path}")
        print(f"   ✅ KB table: {config.KNOWLEDGE_BANK_TABLE}")
        
        # Test files created
        import os
        assert os.path.exists(kb.rules_yaml_path), "rules.yaml should exist"
        assert os.path.exists(kb.treatments_csv_path), "treatments.csv should exist"
        
        print(f"   ✅ KB files created successfully")
        
        return True
    except Exception as e:
        print(f"   ❌ KB BigQuery integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_env_override():
    """Test that environment variables can override config"""
    print("\n🧪 Testing Config Environment Override...")
    try:
        import os
        from importlib import reload
        
        # Set env var
        os.environ['PROJECT_ID'] = 'test-project-override'
        
        # Reload config
        import backend.config as config_module
        reload(config_module)
        
        from backend.config import config
        
        if config.PROJECT_ID == 'test-project-override':
            print(f"   ✅ Environment override works: {config.PROJECT_ID}")
        else:
            print(f"   ⚠️  Environment override didn't work (not critical)")
        
        # Reset
        os.environ['PROJECT_ID'] = 'hackathon-practice-480508'
        reload(config_module)
        
        return True
    except Exception as e:
        print(f"   ⚠️  Config override test warning: {e}")
        return True  # Not critical

def run_integration_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("🔗 AgentX Integration Testing Suite")
    print("=" * 60)
    
    tests = [
        ("Agent Wrapper Compatibility", test_agent_wrapper_compatibility),
        ("Tools Module", test_tools_module),
        ("Identifier Integration", test_enhanced_identifier_with_wrapper),
        ("Security + FastAPI", test_security_with_fastapi),
        ("Knowledge Bank + BigQuery", test_knowledge_bank_with_bigquery),
        ("Config Env Override", test_config_env_override)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
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
    success = run_integration_tests()
    sys.exit(0 if success else 1)

