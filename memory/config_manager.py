import os
import sys
import json

def load_config(filename="config/api_keys.json"):
    """Loads configuration data safely searching multiple locations."""
    possible_paths = []
    
    if hasattr(sys, '_MEIPASS'):
        possible_paths.append(os.path.join(sys._MEIPASS, filename))
    
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        possible_paths.append(os.path.join(exe_dir, filename))
    
    possible_paths.append(os.path.abspath(filename))
    possible_paths.append(os.path.join(os.path.abspath("."), filename))

    full_path = None
    for path in possible_paths:
        if os.path.exists(path):
            full_path = path
            break

    if not full_path:
        raise FileNotFoundError(f"Configuration file not found. Checked paths: {possible_paths}")
    
    with open(full_path, "r") as f:
        return json.load(f)

def get_openai_key():
    """Retrieves the OpenAI API key safely from the configuration file."""
    config = load_config()
    return config.get("openai_api_key", "")