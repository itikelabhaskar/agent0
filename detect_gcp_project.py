"""
Auto-detect GCP project from active gcloud configuration
This ensures the code works with any GCP project automatically
"""
import subprocess
import json
import os
from pathlib import Path

def get_active_gcp_project():
    """
    Get the currently active GCP project from authenticated GCP session
    Falls back through multiple detection methods
    """
    # Method 1: Try Application Default Credentials (MOST RELIABLE - uses logged in account)
    try:
        from google.auth import default
        credentials, project = default()
        if project:
            print(f"✅ Detected GCP project from authenticated session (ADC): {project}")
            return project
    except Exception as e:
        print(f"⚠️  ADC not available: {e}")
    
    # Method 2: Try gcloud command (if gcloud is in PATH)
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            project = result.stdout.strip()
            if project and project != "(unset)":
                print(f"✅ Detected GCP project from gcloud config: {project}")
                return project
    except FileNotFoundError:
        print(f"⚠️  gcloud command not found in PATH")
    except Exception as e:
        print(f"⚠️  Could not run gcloud: {e}")
    
    # Method 3: Try environment variables
    project = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    if project and project != "AUTO_DETECT":
        print(f"✅ Using GCP project from environment variable: {project}")
        return project
    
    # Method 4: Try config file (but skip AUTO_DETECT)
    config_files = ["config.json", "config/dev.local.json"]
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    project = config.get("project_id")
                    if project and project != "AUTO_DETECT":
                        print(f"✅ Using GCP project from {config_file}: {project}")
                        return project
            except Exception:
                pass
    
    print("❌ Could not detect GCP project!")
    print()
    print("   Please authenticate to GCP first:")
    print("   1. Run: gcloud auth application-default login")
    print("   2. Or: gcloud config set project YOUR_PROJECT_ID")
    print("   3. Or: set environment variable: $env:GCP_PROJECT='YOUR_PROJECT_ID'")
    print()
    return None

def update_config_with_detected_project(project_id, dataset="dev_dataset"):
    """
    Update or create config.json with detected project
    """
    config_file = "config.json"
    
    config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file) as f:
                config = json.load(f)
        except Exception:
            pass
    
    # Update project ID
    config["project_id"] = project_id
    config["dataset"] = dataset
    config["mode"] = "local"
    
    # Add table references
    if "week1_table" not in config:
        config["week1_table"] = f"{dataset}.week1"
        config["week2_table"] = f"{dataset}.week2"
        config["week3_table"] = f"{dataset}.week3"
        config["week4_table"] = f"{dataset}.week4"
    
    config["raw_table"] = config.get("raw_table", f"{dataset}.week1")
    config["clean_table"] = config.get("clean_table", f"{dataset}.cleaned_data")
    config["rules_table"] = config.get("rules_table", f"{dataset}.rules")
    config["issues_table"] = config.get("issues_table", f"{dataset}.issues")
    
    # Write back
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Updated {config_file} with project: {project_id}")
    return config

def ensure_project_configured():
    """
    Ensure project is configured - main entry point
    Returns (project_id, dataset)
    """
    project = get_active_gcp_project()
    
    if not project:
        print("\n⚠️  WARNING: No GCP project detected!")
        print("   The application may not work correctly.")
        print("   Run: gcloud config set project YOUR_PROJECT_ID")
        return None, None
    
    # Update config file
    dataset = os.getenv("DATASET", "dev_dataset")
    config = update_config_with_detected_project(project, dataset)
    
    return project, dataset

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 GCP Project Auto-Detection")
    print("=" * 70)
    print()
    
    project, dataset = ensure_project_configured()
    
    if project:
        print()
        print("=" * 70)
        print("✅ Configuration Complete!")
        print("=" * 70)
        print(f"   Project: {project}")
        print(f"   Dataset: {dataset}")
        print()
        print("The application will now use this GCP project automatically.")
        print()
        print("Your friend can run the same code on their laptop and it will")
        print("automatically detect THEIR GCP project from their gcloud config.")
    else:
        print()
        print("=" * 70)
        print("❌ Setup Required")
        print("=" * 70)
        print("Please configure GCP project first:")
        print("   gcloud config set project YOUR_PROJECT_ID")

