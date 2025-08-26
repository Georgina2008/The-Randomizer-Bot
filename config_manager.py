import json
import os

CONFIG_FILE = "bot_config.json"

default_config = {
    "sessions": {},
    "delayed_posts": {}
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return default_config.copy()

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)
