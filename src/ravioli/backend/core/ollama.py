import httpx
import os
from typing import Dict, Any
from sqlalchemy.orm import Session
from ravioli.backend.core.models import SystemSetting
from ravioli.backend.core.config import settings
from ravioli.backend.core.encryption import decrypt_value
from pathlib import Path

def _load_kowalski_persona() -> str:
    """Loads the Kowalski persona dossier from the AI agents directory."""
    try:
        # Resolve path to src/ravioli/ai/agents/Kowalski.md
        persona_path = Path(__file__).resolve().parents[3] / "ai" / "agents" / "Kowalski.md"
        if persona_path.exists():
            return persona_path.read_text()
    except Exception as e:
        print(f"OllamaClient: [WARNING] Failed to load Kowalski dossier: {e}")
    
    # Minimal fallback if file is missing
    return "You are Kowalski, a lead analytics specialist. Clinical and precise. Confirm with 'Tak.'"

KOWALSKI_PERSONA = _load_kowalski_persona()

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

    async def _generate(self, prompt: str, task_name: str, temperature: float = 0.5, num_predict: int = 300) -> str:
        """Helper method to handle the actual API call to Ollama with logging."""
        import time
        start_time = time.time()
        
        url = f"{self.base_url.rstrip('/')}/api/generate"
        headers = {}
        if self.mode == "cloud" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        print(f"OllamaClient: [INFO] URL: {url}", flush=True)
        print(f"OllamaClient: [INFO] Task: {task_name}", flush=True)
        print(f"OllamaClient: [INFO] Model: {self.model}", flush=True)
        print(f"OllamaClient: [INFO] Data Size: {len(prompt)} chars", flush=True)

        # Final safety truncation: most models can't handle more than ~100k characters in a prompt
        if len(prompt) > 100000:
            print(f"OllamaClient: [WARNING] Truncating prompt from {len(prompt)} to 100000 characters", flush=True)
            prompt = prompt[:100000] + "\n... [TRUNCATED DUE TO SIZE] ..."

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict
            }
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    print(f"OllamaClient: [ERROR] API returned {response.status_code}", flush=True)
                    print(f"OllamaClient: [ERROR] Response: {response.text[:500]}", flush=True)
                    if response.status_code == 401:
                        raise Exception("Ollama authentication failed. Check your API Key.")
                    response.raise_for_status()
                
                result = response.json()
                content = result.get("response", "").strip()
                
                duration = time.time() - start_time
                print(f"OllamaClient: [SUCCESS] {task_name} completed in {duration:.2f}s", flush=True)
                return content
        except Exception as e:
            duration = time.time() - start_time
            print(f"OllamaClient: [EXCEPTION] {task_name} failed after {duration:.2f}s: {str(e)}", flush=True)
            raise e

    async def generate_quick_insight(self, filename: str, sample_data: str) -> str:
        """
        Generate key insights for a data asset based on its content.
        """
        prompt = f"""{KOWALSKI_PERSONA}
Task: Analyze the statistical profile of the dataset "{filename}" and provide 8-10 concise bullet points of clinical insights.
Focus on quantifiable trends and anomalies across the ENTIRE dataset.
Return ONLY the bullet points, followed by a Polish confirmation line.

Dataset Profile:
---
{sample_data}
---

Key Insights:"""

        try:
            return await self._generate(prompt, "Quick Insight", temperature=0.5, num_predict=500)
        except Exception:
            # Fallback to a generic message if AI fails
            return f"> [!IMPORTANT]\n> **SIMULATED INSIGHTS**: The AI engine is currently unreachable. These are baseline patterns.\n\n- **Volume Concentration**: Data shows regular patterns across primary dimensions.\n- **Dimensional Depth**: High correlation observed between key indicators.\n- **Velocity Trend**: Stable trajectory in engagement."

    async def generate_assumptions(self, filename: str, sample_data: str) -> str:
        """
        Generate potential assumptions made during data analysis.
        """
        prompt = f"""{KOWALSKI_PERSONA}
Task: Analyze the statistical profile of "{filename}" and provide 2-3 clinical assumptions for analysis.
Return ONLY the bullet points, followed by a Polish confirmation line.

Dataset Profile:
---
{sample_data}
---

Assumptions:"""

        try:
            return await self._generate(prompt, "Assumptions", temperature=0.4, num_predict=300)
        except Exception:
            return "- Data is representative of the period/context specified.\n- Column names are accurately descriptive of their contents."

    async def generate_limitations(self, filename: str, sample_data: str) -> str:
        """
        Generate potential limitations and issues for the data.
        """
        prompt = f"""{KOWALSKI_PERSONA}
Task: Analyze the statistical profile of "{filename}" and identify 2-3 clinical limitations or data quality issues.
Return ONLY the bullet points, followed by a Polish confirmation line.

Dataset Profile:
---
{sample_data}
---

Limitations & Issues:"""

        try:
            return await self._generate(prompt, "Limitations", temperature=0.4, num_predict=300)
        except Exception:
            return "- Limited context on data collection methodology.\n- Sample size may not capture all edge case variance."
