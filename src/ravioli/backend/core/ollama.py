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
You are a professional data engineer. Generate an extremely concise, single-sentence description for a data asset.
The asset is named "{filename}".
Here is a preview of the data (CSV format):
---
{sample_data}
---
The description should focus on what the data represents.
Be clinical, objective, and avoid ALL filler words. Max 15 words.
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
Task: Analyze the statistical profile of "{filename}" and provide 3-5 high-impact, extremely concise clinical insights.
Prioritize the most significant quantifiable trends and anomalies.
Minimize "Speed to Insights": be direct, precise, and brief.
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
Task: Analyze the statistical profile of "{filename}" and provide 2 extremely concise clinical assumptions.
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
Task: Analyze the statistical profile of "{filename}" and identify 1-2 critical clinical limitations.
Be extremely brief. Return ONLY the bullet points, followed by a Polish confirmation line.

Dataset Profile:
---
{sample_data}
---

Limitations & Issues:"""

        try:
            return await self._generate(prompt, "Limitations", temperature=0.4, num_predict=300)
        except Exception:
            return "- Limited context on data collection methodology.\n- Sample size may not capture all edge case variance."

    async def generate_followup_questions(self, filename: str, summary: str, sample_data: str) -> list[str]:
        """
        Generate 3-4 insightful follow-up questions based on the summary and data profile.
        """
        prompt = f"""{KOWALSKI_PERSONA}
Task: Based on the Summary and Profile for "{filename}", generate 3 extremely concise, professional follow-up questions.
The goal is to minimize "Speed to Insights". Be direct and analytical.
Return ONLY the questions, one per line, starting with a dash (-). No confirmation line.

Executive Summary:
{summary}

Dataset Profile Sample:
{sample_data[:2000]}

Follow-up Questions:"""

        try:
            content = await self._generate(prompt, "Follow-up Questions", temperature=0.6, num_predict=400)
            # Parse bullet points into a list
            questions = [q.strip("- ").strip() for q in content.split('\n') if q.strip().startswith("-")]
            # Filter out empty or too short questions
            questions = [q for q in questions if len(q) > 10][:4]
            return questions
        except Exception:
            return [
                "What are the primary drivers behind the observed volume concentration?",
                "Are there specific time periods where the anomalies are more prevalent?",
                "How do these trends compare to historical baseline patterns?",
                "What is the impact of the identified limitations on the overall analysis?"
            ]

    async def generate_answer(self, filename: str, summary: str, context: str, question: str) -> str:
        """
        Generate a clinical, precise answer to a user question based on data context.
        """
        prompt = f"""{KOWALSKI_PERSONA}
Context: Analyzing dataset "{filename}".
Summary: {summary}
Context: {context}

Question: {question}

Task: Provide a clinical, extremely precise, and data-driven answer. 
Brevity is mandatory. Minimize "Speed to Insights". Max 3 sentences.
Return in Markdown format.
Answer:"""

        try:
            return await self._generate(prompt, "Agent Answer", temperature=0.4, num_predict=1000)
        except Exception as e:
            return f"> [!WARNING]\n> **Neural Link Interrupted**: {str(e)}\n\nKowalski is currently unable to process this request. Please check your AI node connection."

    async def stream_answer(self, filename: str, summary: str, context: str, question: str):
        """
        Stream a clinical, precise answer to a user question.
        Yields tokens as they are generated.
        """
        prompt = f"""{KOWALSKI_PERSONA}
Context: Analyzing dataset "{filename}".
Summary: {summary}
Context: {context}

Question: {question}

Task: Provide a clinical, extremely precise, and data-driven answer. 
Brevity is mandatory. Minimize "Speed to Insights". Max 3 sentences.
Return in Markdown format.
Answer:"""

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.4,
                "num_predict": 1000
            }
        }

        import httpx
        import json
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done", False):
                            break
        except Exception as e:
            yield f"\n\n> [!ERROR]\n> **Stream Interrupted**: {str(e)}"
