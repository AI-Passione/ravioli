import httpx
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ravioli.backend.core.models import SystemSetting
from ravioli.backend.core.config import settings
from ravioli.backend.core.encryption import decrypt_value

class OllamaClient:
    def __init__(self, db: Session):
        self.db = db
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load Ollama configuration from the database, falling back to app settings."""
        setting = self.db.query(SystemSetting).filter(SystemSetting.key == "ollama").first()
        
        if setting and setting.value:
            config = dict(setting.value)
            # Decrypt API key if present
            if "api_key" in config and config["api_key"]:
                config["api_key"] = decrypt_value(config["api_key"])
            return config
            
        # Fallback to defaults from config.py
        return {
            "mode": "default",
            "base_url": settings.ollama_host,
            "default_model": settings.ollama_model,
            "api_key": ""
        }

    @property
    def base_url(self) -> str:
        return self._config.get("base_url", settings.ollama_host)

    @property
    def model(self) -> str:
        return self._config.get("default_model", settings.ollama_model)

    @property
    def api_key(self) -> str:
        return self._config.get("api_key", "")

    async def generate_description(self, filename: str, sample_data: str) -> str:
        """
        Generate a professional, concise description for a data asset based on its name and content.
        """
        prompt = f"""
You are a professional data engineer. Generate a concise, one-sentence description for a data asset.
The asset is named "{filename}".
Here is a preview of the data (CSV format):
---
{sample_data}
---
The description should focus on what the data represents and its primary utility.
Be professional, objective, and avoid filler words.
Description:"""

        url = f"{self.base_url.rstrip('/')}/api/generate"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 100
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                description = result.get("response", "").strip()
                
                # Remove quotes if the model wrapped the description
                if description.startswith('"') and description.endswith('"'):
                    description = description[1:-1]
                
                return description
        except Exception as e:
            raise Exception(f"Ollama generation failed: {str(e)}")
