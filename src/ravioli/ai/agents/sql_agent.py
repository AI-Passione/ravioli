import json
import logging
import re
import httpx
import os
import pandas as pd
from typing import Dict, Any, List, Optional, AsyncGenerator
from ravioli.backend.core.config import settings
from ravioli.backend.data.olap.duckdb_manager import duckdb_manager
from ravioli.backend.core.models import SystemSetting
from ravioli.backend.core.encryption import decrypt_value

logger = logging.getLogger(__name__)

class KowalskiSQLAgent:
    """
    A surgical SQL agent for Kowalski.
    Uses duckdb-nsql for SQL generation and gemma3:4b for reasoning/formatting.
    Implements aggressive RAM optimization by swapping models.
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self._config = self._load_config()
        self.model_sql = "duckdb-nsql"
        self.model_persona = "gemma3:4b"

    def _load_config(self) -> Dict[str, Any]:
        """Load Ollama configuration from the database, falling back to app settings."""
        if self.db_session:
            try:
                setting = self.db_session.query(SystemSetting).filter(SystemSetting.key == "ollama").first()
                if setting and setting.value:
                    config = dict(setting.value)
                    # Decrypt API key if present
                    if "api_key" in config and config["api_key"]:
                        try:
                            config["api_key"] = decrypt_value(config["api_key"])
                        except Exception as e:
                            logger.error(f"KowalskiSQLAgent: Decryption failed: {e}")
                    return config
            except Exception as e:
                logger.error(f"KowalskiSQLAgent: Error loading config from DB: {e}")

        return {
            "mode": "default",
            "base_url": settings.ollama_host,
            "default_model": settings.ollama_model,
            "api_key": ""
        }

    @property
    def mode(self) -> str:
        return self._config.get("mode", "default")

    @property
    def api_key(self) -> str:
        return self._config.get("api_key", "")

    @property
    def ollama_host(self) -> str:
        if self.mode == "cloud":
            return "https://api.ollama.com"
            
        url = self._config.get("base_url", settings.ollama_host)
        # Handle Docker-to-Host communication
        if "localhost" in url or "127.0.0.1" in url or "ollama" in url:
            if os.path.exists("/.dockerenv"):
                return url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal").replace("ollama", "host.docker.internal")
        return url

    async def _generate(self, prompt: str, model: str, temperature: float = 0.1, keep_alive: Any = "5m") -> str:
        url = f"{self.ollama_host.rstrip('/')}/api/generate"
        headers = {}
        if self.mode == "cloud" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Only log RAM optimization for local mode
        if self.mode != "cloud":
            logger.info(f"Ollama: [RAM OPTIMIZATION] Loading {model} (keep_alive={keep_alive})...")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": keep_alive if self.mode != "cloud" else "5m",
            "options": {
                "temperature": temperature,
                "num_predict": 1000
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Ollama: [SUCCESS] Task completed by {model} ({self.mode})")
                return response.json().get("response", "").strip()
        except httpx.ConnectError as e:
            logger.error(f"Ollama: [ERROR] Connection failed to {url}. Is Ollama running? Error: {e}")
            raise Exception(f"Kowalski: Statistical Brain unreachable at {self.ollama_host}. Ensure AI node is active.")
        except Exception as e:
            logger.error(f"Ollama: [EXCEPTION] {e}")
            raise e

    async def unload_model(self, model: str):
        """Explicitly unloads a model from RAM. SKIPPED in Cloud mode."""
        if self.mode == "cloud":
            return
            
        logger.info(f"Ollama: [RAM OPTIMIZATION] Requesting UNLOAD for model: {model}")
        url = f"{self.ollama_host.rstrip('/')}/api/generate"
        
        payload = {"model": model, "keep_alive": 0}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
            logger.info(f"Ollama: [RAM OPTIMIZATION] {model} has been evicted from RAM.")
        except Exception as e:
            logger.warning(f"Ollama: [RAM OPTIMIZATION] Failed to unload {model}: {e}")

    def _get_schema(self, table_name: str, schema_name: str = "main") -> str:
        """Extracts the CREATE TABLE statement for context."""
        try:
            sql = "SELECT sql FROM duckdb_tables WHERE schema_name = ? AND table_name = ?"
            result = duckdb_manager.connection.execute(sql, [schema_name, table_name]).fetchone()
            if result and result[0]:
                return result[0]
            
            cols = duckdb_manager.connection.execute(f'DESCRIBE "{schema_name}"."{table_name}"').fetchall()
            return f"Table {table_name} columns: {', '.join([c[0] for c in cols])}"
        except Exception as e:
            logger.error(f"Error getting schema for {table_name}: {e}")
            return f"Error retrieving schema for {table_name}."

    async def generate_sql(self, question: str, table_name: str, schema_name: str = "main") -> Optional[str]:
        """Generates SQL using duckdb-nsql (or default model in cloud)."""
        schema = self._get_schema(table_name, schema_name)
        
        prompt = f"""### Instruction:
Your query should be compatible with DuckDB. Use the provided schema.
### Schema:
{schema}
### Question:
{question}
### Response (use duckdb):
"""
        target_model = self.model_sql
        if self.mode == "cloud":
            target_model = self._config.get("default_model", self.model_persona)

        try:
            if self.mode != "cloud":
                await self.unload_model(self.model_persona)
            
            logger.info(f"Ollama: [BRAIN] Generating surgical SQL via {target_model}...")
            response = await self._generate(prompt, target_model, keep_alive=0 if self.mode != "cloud" else "5m")
            
            sql = response.strip()
            # Handle markdown wrapping
            if "```sql" in sql:
                sql = re.search(r"```sql\s*(.*?)\s*```", sql, re.DOTALL).group(1)
            elif "```" in sql:
                sql = re.search(r"```\s*(.*?)\s*```", sql, re.DOTALL).group(1)
            
            # Remove hallucinations like "duckdb" or preamble text
            # Find the first occurrence of SELECT
            select_match = re.search(r"(SELECT\s+.*)", sql, re.IGNORECASE | re.DOTALL)
            if select_match:
                sql = select_match.group(1).strip()
            
            # Clean trailing characters
            sql = sql.split(';')[0].strip()
            
            logger.info(f"Ollama: [BRAIN] SQL generated successfully: {sql}")
            return sql
        except Exception as e:
            logger.error(f"SQL Generation failed: {e}")
            return None

    async def create_viz_payload(self, sql: str, original_question: str) -> Dict[str, Any]:
        """
        Executes SQL and uses LLM to decide on best chart type and formatting.
        """
        try:
            logger.info("Ollama: [VOICE] Kowalski is analyzing query results for visualization...")
            
            df = duckdb_manager.connection.execute(sql).fetchdf()
            if df.empty:
                return {"type": "error", "message": "Query returned no data."}

            for col in df.select_dtypes(include=['datetime64', 'datetimetz']).columns:
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            data_sample = df.head(5).to_dict(orient='records')
            columns = df.columns.tolist()

            prompt = f"""You are Kowalski, a data visualization expert.
Based on this data sample and the user's question, decide on the BEST Chart.js configuration.
Question: "{original_question}"
Columns: {columns}
Sample Data: {json.dumps(data_sample)}

Respond ONLY with a JSON object containing:
- "chart_type": "bar", "line", "pie", or "scatter"
- "labels_column": The column name for X-axis
- "values_columns": List of column names for Y-axis
- "title": A clinical title for the chart

JSON:"""
            
            viz_config_raw = await self._generate(prompt, self.model_persona, temperature=0.1)
            match = re.search(r'\{.*\}', viz_config_raw, re.DOTALL)
            if not match:
                config = {
                    "chart_type": "bar",
                    "labels_column": columns[0],
                    "values_columns": [columns[1]] if len(columns) > 1 else [],
                    "title": "Data Visualization"
                }
            else:
                config = json.loads(match.group(0))

            labels = df[config["labels_column"]].tolist()
            datasets = []
            
            colors = [
                "rgba(0, 245, 212, 0.6)",  # Neon Teal
                "rgba(18, 113, 255, 0.6)",  # Electric Blue
                "rgba(157, 78, 221, 0.6)",  # Deep Purple
                "rgba(255, 0, 110, 0.6)",   # Magenta
            ]
            border_colors = [
                "rgba(0, 245, 212, 1)",
                "rgba(18, 113, 255, 1)",
                "rgba(157, 78, 221, 1)",
                "rgba(255, 0, 110, 1)",
            ]

            for i, col in enumerate(config["values_columns"]):
                datasets.append({
                    "label": col,
                    "data": df[col].tolist(),
                    "backgroundColor": colors[i % len(colors)],
                    "borderColor": border_colors[i % len(colors)],
                    "borderWidth": 2,
                    "borderRadius": 8,
                    "tension": 0.4 
                })

            logger.info(f"Ollama: [VOICE] Visualization strategy locked: {config['chart_type']} ({config['title']})")
            return {
                "type": "chart",
                "chart_type": config["chart_type"],
                "title": config["title"],
                "data": {
                    "labels": labels,
                    "datasets": datasets
                }
            }
        except Exception as e:
            logger.error(f"Visualization payload creation failed: {e}")
            return {"type": "error", "message": str(e)}

    async def process_question(self, question: str, table_name: str, schema_name: str = "main") -> AsyncGenerator[Any, None]:
        """
        High-level entry point to process a question and get either text or viz.
        Yields strings (status updates) and finally a dict (result).
        """
        prompt = f"""Is this a question that requires a data visualization (chart, plot, graph)? 
Question: "{question}"
Respond ONLY with 'YES' or 'NO'."""
        
        logger.info(f"Ollama: [ANALYSIS] Analyzing Operator query: '{question}'")
        try:
            decision = await self._generate(prompt, self.model_persona)
            
            if "YES" in decision.upper():
                yield "_[Kowalski is engaging the Statistical Brain for visualization...]_"
                logger.info("Ollama: [ANALYSIS] Visualization required. Engaging SQL Brain.")
                
                yield "_[Generating surgical SQL query...]_"
                sql = await self.generate_sql(question, table_name, schema_name)
                
                if sql:
                    yield f"_[Executing query and assembling vision strategy...]_"
                    viz_payload = await self.create_viz_payload(sql, question)
                    
                    if viz_payload.get("type") == "error":
                        logger.error(f"Visualization failed: {viz_payload.get('message')}")
                        yield f"> [!WARNING]\n> **Visualization Bypass**: {viz_payload.get('message')}\n\nFalling back to textual analysis. Zrozumiałem."
                    else:
                        yield {
                            "answer_type": "viz",
                            "sql": sql,
                            "viz": viz_payload
                        }
                        return
                else:
                    yield f"> [!WARNING]\n> **Neural Synthesis Failed**: Could not translate the request into a valid query. Falling back to textual reasoning."
            
            logger.info("Ollama: [ANALYSIS] Standard textual response sufficient.")
            yield {"answer_type": "text"}
        except Exception as e:
            logger.error(f"Ollama: [ERROR] Process question failed: {e}")
            yield f"> [!ERROR]\n> **Neural Link Failed**: {str(e)}"
            yield {"answer_type": "text", "error": str(e)}
