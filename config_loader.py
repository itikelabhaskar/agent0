# config_loader.py
import json
import os
import subprocess

DEFAULT_PATHS = [
    "config.json",                 # explicit config (ignored in git)
    "config/dev.local.json",       # dev local default
]

def get_active_gcp_project():
    """Auto-detect GCP project from authenticated GCP session"""
    # Method 1: Try Application Default Credentials (PRIMARY - uses logged in account)
    try:
        from google.auth import default
        credentials, project = default()
        if project:
            return project
    except Exception:
        pass
    
    # Method 2: Try gcloud command
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
                return project
    except Exception:
        pass
    
    # Method 3: Try environment variables
    project = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    if project and project != "AUTO_DETECT":
        return project
    
    return None

def load_config():
    # priority: explicit config.json (local), then ENV override, then dev.local
    env_mode = os.getenv("AGENTX_CONFIG_MODE", "").strip()
    if os.path.exists("config.json"):
        path = "config.json"
    elif env_mode.lower() == "sandbox" and os.path.exists("config/prod.sandbox.json"):
        path = "config/prod.sandbox.json"
    elif env_mode.lower() == "dev" and os.path.exists("config/dev.local.json"):
        path = "config/dev.local.json"
    else:
        # find first existing default
        path = next((p for p in DEFAULT_PATHS if os.path.exists(p)), None)

    if not path:
        raise FileNotFoundError("No config found. Create config.json or config/dev.local.json or set AGENTX_CONFIG_MODE env var.")
    with open(path) as f:
        cfg = json.load(f)
    
    # Auto-detect project if set to AUTO_DETECT
    if cfg.get("project_id") == "AUTO_DETECT":
        detected_project = get_active_gcp_project()
        if detected_project:
            cfg["project_id"] = detected_project
            print(f"✅ Auto-detected GCP project: {detected_project}")
        else:
            print("⚠️  Could not auto-detect GCP project. Using placeholder.")
            cfg["project_id"] = "PLEASE_SET_PROJECT"
    
    # Track source file for debugging
    cfg["__source__"] = os.path.abspath(path)
    return cfg

CONFIG = load_config()
