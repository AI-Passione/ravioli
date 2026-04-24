import httpx
import os
from typing import Dict, Any
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
        try:
            setting = self.db.query(SystemSetting).filter(SystemSetting.key == "ollama").first()
            
            if setting and setting.value:
                config = dict(setting.value)
                print(f"OllamaClient: Found setting in DB: {config.get('mode')}")
                # Decrypt API key if present
                if "api_key" in config and config["api_key"]:
                    try:
                        config["api_key"] = decrypt_value(config["api_key"])
                    except Exception as e:
                        print(f"OllamaClient: Decryption failed: {e}")
                return config
            
            print("OllamaClient: No setting found in DB, using defaults")
        except Exception as e:
            print(f"OllamaClient: Error loading config from DB: {e}")

        # Fallback to defaults from config.py
        return {
            "mode": "default",
            "base_url": settings.ollama_host,
            "default_model": settings.ollama_model,
            "api_key": ""
        }

    @property
    def base_url(self) -> str:
        # If cloud mode, use the fixed cloud URL
        if self.mode == "cloud":
            return "https://api.ollama.com"
            
        url = self._config.get("base_url", settings.ollama_host)
        # Handle Docker-to-Host communication
        if "localhost" in url or "127.0.0.1" in url:
            # Check if running inside a container
            if os.path.exists("/.dockerenv"):
                return url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")
        return url

    @property
    def model(self) -> str:
        return self._config.get("default_model", settings.ollama_model)

    @property
    def api_key(self) -> str:
        return self._config.get("api_key") or ""

    @property
    def mode(self) -> str:
        return self._config.get("mode", "default")

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
        # Only send API key in cloud mode
        if self.mode == "cloud" and self.api_key:
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
                
                if response.status_code == 401:
                    raise Exception("Ollama authentication failed. Please check your API key in Settings.")
                
                response.raise_for_status()
                result = response.json()
                description = result.get("response", "").strip()
                
                # Remove quotes if the model wrapped the description
                if description.startswith('"') and description.endswith('"'):
                    description = description[1:-1]
                
                return description
        except httpx.ConnectError:
            raise Exception(f"Could not connect to Ollama at {self.base_url}. Make sure it's running.")
        except Exception as e:
            raise Exception(f"Ollama generation failed: {str(e)}")

    async def generate_quick_insight(self, filename: str, sample_data: str) -> str:
        """
        Generate key insights for a data asset based on its content.
        """
        prompt = f"""
You are a professional data scientist. Analyze the following data sample from "{filename}" and provide 4-5 concise bullet points of key insights.
Focus on identifying potential trends, distributions, or interesting relationships.
Return ONLY the bullet points, starting each with a dash (-).

Data Preview (CSV):
---
{sample_data}
---

Key Insights:"""

        url = f"{self.base_url.rstrip('/')}/api/generate"
        headers = {}
        if self.mode == "cloud" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.5,
                "num_predict": 300
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 401:
                    raise Exception("Ollama authentication failed.")
                response.raise_for_status()
                result = response.json()
                return result.get("response", "").strip()
        except Exception as e:
            # Fallback to a generic message if AI fails
            return f"> [!IMPORTANT]\n> **SIMULATED INSIGHTS**: The AI engine is currently unreachable. These are baseline patterns.\n\n- **Volume Concentration**: Data shows regular patterns across primary dimensions.\n- **Dimensional Depth**: High correlation observed between key indicators.\n- **Velocity Trend**: Stable trajectory in engagement."

    async def generate_assumptions(self, filename: str, sample_data: str) -> str:
        """
        Generate potential assumptions made during data analysis.
        """
        prompt = f"""
You are a professional data scientist. Analyze the following data sample from "{filename}" and provide 2-3 logical assumptions that would be made during its analysis (e.g. data completeness, representativeness, or column definitions).
Return ONLY the bullet points, starting each with a dash (-).

Data Preview (CSV):
---
{sample_data}
---

Assumptions:"""

        url = f"{self.base_url.rstrip('/')}/api/generate"
        headers = {}
        if self.mode == "cloud" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 200
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "").strip()
        except Exception:
            return "- Data is representative of the period/context specified.\n- Column names are accurately descriptive of their contents."

    async def generate_limitations(self, filename: str, sample_data: str) -> str:
        """
        Generate potential limitations and issues for the data.
        """
        prompt = f"""
You are a professional data scientist. Analyze the following data sample from "{filename}" and provide 2-3 concise bullet points regarding potential limitations or data quality issues (e.g. sample size, potential bias, or missing context).
Return ONLY the bullet points, starting each with a dash (-).

Data Preview (CSV):
---
{sample_data}
---

Limitations & Issues:"""

        url = f"{self.base_url.rstrip('/')}/api/generate"
        headers = {}
        if self.mode == "cloud" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 200
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "").strip()
        except Exception:
            return "- Limited context on data collection methodology.\n- Sample size may not capture all edge case variance."
