"""
AgentX Test Runner
Run all tests in organized structure
"""
import sys
import os
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests and report results"""
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Add project root to PYTHONPATH so imports work
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    # Set UTF-8 encoding for subprocess
    env['PYTHONIOENCODING'] = 'utf-8'
    
    print("=" * 70)
    print("AGENTX TEST SUITE")
    print("=" * 70)
    print(f"Running from: {project_root}")
    
    test_results = []
    
    # Unit tests
    print("\n[UNIT TESTS]")
    print("-" * 70)
    
    unit_tests = [
        "tests/unit/test_agents_quick.py",
        "tests/unit/test_orchestrator_quick.py",
        "tests/unit/test_new_components.py"
    ]
    
    for test in unit_tests:
        if Path(test).exists():
            print(f"\n▶ Running {test}...")
            result = subprocess.run(
                [sys.executable, test],
                capture_output=True,
                text=True,
                cwd=project_root,
                env=env,
                encoding='utf-8',
                errors='replace'  # Replace encoding errors instead of failing
            )
            success = result.returncode == 0
            test_results.append((test, success))
            
            if success:
                print(f"  [PASS]")
            else:
                print(f"  [FAIL]")
                if result.stderr:
                    # Clean stderr for display
                    error_msg = result.stderr[:300].replace('\n', ' ')
                    print(f"  Error: {error_msg}")
        else:
            print(f"  [SKIP] {test} not found")
    
    # Integration tests
    print("\n[INTEGRATION TESTS]")
    print("-" * 70)
    
    integration_tests = [
        "tests/integration/test_backend_integration.py",
        "tests/integration/test_bq_setup.py",
        "tests/integration/test_final_features.py"
    ]
    
    for test in integration_tests:
        if Path(test).exists():
            print(f"\n▶ Running {test}...")
            result = subprocess.run(
                [sys.executable, test],
                capture_output=True,
                text=True,
                cwd=project_root,
                env=env,
                encoding='utf-8',
                errors='replace'  # Replace encoding errors instead of failing
            )
            success = result.returncode == 0
            test_results.append((test, success))
            
            if success:
                print(f"  [PASS]")
            else:
                print(f"  [FAIL]")
                if result.stderr:
                    # Clean stderr for display
                    error_msg = result.stderr[:300].replace('\n', ' ')
                    print(f"  Error: {error_msg}")
        else:
            print(f"  [SKIP] {test} not found")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    print(f"\n[+] Passed: {passed}/{total}")
    print(f"[-] Failed: {total - passed}/{total}")
    print(f"[%] Pass Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Review output above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())

