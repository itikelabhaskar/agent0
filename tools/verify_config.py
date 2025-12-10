# tools/verify_config.py
import sys
import os

# Add parent directory to path for config_loader import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import CONFIG

print("Loaded CONFIG from:", os.path.abspath(CONFIG.get("__source__", "config.json (unknown)")))
print("Mode:", CONFIG.get("mode"))
print("Project ID:", CONFIG.get("project_id"))
print("Dataset:", CONFIG.get("dataset"))
print("Raw table:", CONFIG.get("raw_table"))
print("Rules table:", CONFIG.get("rules_table"))
print("Vertex model:", CONFIG.get("vertex_model"))

# Build fully-qualified names
proj = CONFIG.get("project_id")
ds = CONFIG.get("dataset")
if proj and ds:
    print("Fully qualified example names:")
    print("  rules:", f"{proj}.{ds}.rules")
    print("  issues:", f"{proj}.{ds}.issues")
else:
    print("Project/dataset not set in config. Please check config files.")
