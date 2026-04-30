import httpx
import os
import json
import time
from typing import Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session
from ravioli.backend.core.models import SystemSetting
from ravioli.backend.core.config import settings
from ravioli.backend.core.encryption import decrypt_value
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Core backend client for communicating with Ollama nodes.
    Handles configuration, encryption, connectivity, and raw generation.
    """
    def __init__(self, db: Session):
        self.db = db
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load Ollama configuration from the database, falling back to app settings."""
        try:
            setting = self.db.query(SystemSetting).filter(SystemSetting.key == "ollama").first()
            
            if setting and setting.value:
                config = dict(setting.value)
                if "api_key" in config and config["api_key"]:
                    try:
                        config["api_key"] = decrypt_value(config["api_key"])
                    except Exception as e:
                        logger.error(f"OllamaClient: Decryption failed: {e}")
                return config
        except Exception as e:
            logger.error(f"OllamaClient: Error loading config from DB: {e}")

        return {
            "mode": "default",
            "base_url": settings.ollama_host,
            "default_model": settings.ollama_model,
            "api_key": ""
        }

    @property
    def base_url(self) -> str:
        if self.mode == "cloud":
            return "https://api.ollama.com"
            
        url = self._config.get("base_url", settings.ollama_host)
        if "localhost" in url or "127.0.0.1" in url or "ollama" in url:
            if os.path.exists("/.dockerenv"):
                return url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal").replace("ollama", "host.docker.internal")
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

    async def check_connection(self) -> bool:
        """Verifies if the Ollama node is reachable."""
        url = f"{self.base_url.rstrip('/')}/api/tags"
        headers = {}
        if self.mode == "cloud" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False

    async def unload_model(self, model: str = None):
        """Explicitly unloads a model from RAM."""
        target = model or self.model
        logger.info(f"OllamaClient: Unloading model {target}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(f"{self.base_url.rstrip('/')}/api/generate", json={
                    "model": target,
                    "keep_alive": 0
                })
        except Exception as e:
            logger.warning(f"OllamaClient: Failed to unload model: {e}")

    async def generate(self, prompt: str, task_name: str, temperature: float = 0.5, num_predict: int = 300) -> str:
        """Raw generation engine for synchronous calls."""
        start_time = time.time()
        url = f"{self.base_url.rstrip('/')}/api/generate"
        headers = {}
        if self.mode == "cloud" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Truncate if too large
        if len(prompt) > 100000:
            prompt = prompt[:100000] + "\n... [TRUNCATED] ..."

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "5m",
            "options": {"temperature": temperature, "num_predict": num_predict}
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                content = response.json().get("response", "").strip()
                logger.info(f"OllamaClient: [SUCCESS] {task_name} completed in {time.time() - start_time:.2f}s")
                return content
        except Exception as e:
            logger.error(f"OllamaClient: [EXCEPTION] {task_name} failed: {str(e)}")
            raise e

    async def stream(self, prompt: str, temperature: float = 0.4, num_predict: int = 1000) -> AsyncGenerator[str, None]:
        """Raw token streaming engine."""
        url = f"{self.base_url.rstrip('/')}/api/generate"
        headers = {}
        if self.mode == "cloud" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "keep_alive": "5m",
            "options": {"temperature": temperature, "num_predict": num_predict}
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        yield f"\n\n> [!ERROR]\n> **Stream Error ({response.status_code})**"
                        return

                    async for line in response.aiter_lines():
                        if not line or not line.strip(): continue
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token: yield token
                            if data.get("done", False): break
                        except json.JSONDecodeError: continue
        except Exception as e:
            logger.error(f"OllamaClient: [EXCEPTION] Stream interrupted: {str(e)}")
            yield f"\n\n> [!ERROR]\n> **Stream Interrupted**"
