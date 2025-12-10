# config_loader.py
import json
import os

DEFAULT_PATHS = [
    "config.json",                 # explicit config (ignored in git)
    "config/dev.local.json",       # dev local default
]

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
    
    # Track source file for debugging
    cfg["__source__"] = os.path.abspath(path)
    return cfg

CONFIG = load_config()
