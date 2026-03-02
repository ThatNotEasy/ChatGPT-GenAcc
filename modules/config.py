"""
Configuration management module for ChatGPT Account Creator
"""
import json
import os


class Config:
    """Handles loading and managing configuration from config.json"""

    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from config.json or create default if not exists"""
        default_config = {
            "max_workers": 3,
            "headless": False,
            "slow_mo": 1000,
            "timeout": 30000,
            "password": None
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                default_config.update(config)
                return default_config
            else:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            # Return defaults if there's an error
            return default_config

    def get(self, key, default=None):
        """Get a configuration value by key"""
        return self.config.get(key, default)

    def validate_password(self):
        """Validate that password exists and meets minimum requirements"""
        password = self.config.get("password")
        if not password:
            return False, "No password found in config.json! Please add a 'password' field to config.json"
        if len(password) < 12:
            return False, f"Password is only {len(password)} characters. ChatGPT requires at least 12 characters."
        return True, None
