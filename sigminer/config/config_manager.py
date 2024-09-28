import os
import json


class ConfigManager:
    CONFIG_DIR = os.path.join(
        os.path.expanduser("~"), "Library", "Application Support", "sigminer"
    )
    CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self):
        if os.path.exists(self.CONFIG_PATH):
            with open(self.CONFIG_PATH, "r") as f:
                return json.load(f)
        return {}

    def save_config(self):
        os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
        with open(self.CONFIG_PATH, "w") as f:
            json.dump(self.config, f)

    def set_client_id(self, client_id):
        self.config["CLIENT_ID"] = client_id
        self.save_config()

    def set_tenant_id(self, tenant_id):
        self.config["TENANT_ID"] = tenant_id
        self.save_config()

    def get_client_id(self):
        return self.config.get("CLIENT_ID")

    def get_tenant_id(self):
        return self.config.get("TENANT_ID")

    def set_api_key(self, api_key):
        self.config["API_KEY"] = api_key
        self.save_config()
        # Update the environment variable when the API key changes
        os.environ["OPENAI_API_KEY"] = api_key

    def get_api_key(self):
        return self.config.get("API_KEY")

    def save_preset(self, preset_name, preset_data):
        self.config[preset_name] = preset_data
        self.save_config()

    def get_preset(self, preset_name):
        return self.config.get(preset_name, {})

    def get_all_presets(self):
        return [
            key
            for key in self.config.keys()
            if key not in ["CLIENT_ID", "TENANT_ID", "API_KEY"]
        ]

    def delete_preset(self, preset_name):
        if preset_name in self.config:
            del self.config[preset_name]
            self.save_config()
        else:
            raise KeyError(f"Preset '{preset_name}' not found.")
