import json
import logging
import re
import httpx
import pandas as pd
from typing import Dict, Any, List, Optional
from ravioli.backend.core.config import settings
from ravioli.backend.data.olap.duckdb_manager import duckdb_manager

logger = logging.getLogger(__name__)

class KowalskiSQLAgent:
    """
    A surgical SQL agent for Kowalski.
    Uses duckdb-nsql for SQL generation and gemma3:4b for reasoning/formatting.
    Implements aggressive RAM optimization by swapping models.
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.ollama_host = settings.ollama_host
        self.model_sql = "duckdb-nsql"
        self.model_persona = "gemma3:4b"

    async def _generate(self, prompt: str, model: str, temperature: float = 0.1, keep_alive: Any = "5m") -> str:
        url = f"{self.ollama_host.rstrip('/')}/api/generate"
        
        # Handle Docker-to-Host communication for Ollama
        if "localhost" in url or "127.0.0.1" in url:
            import os
            if os.path.exists("/.dockerenv"):
                url = url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")

        logger.info(f"Ollama: [RAM OPTIMIZATION] Loading {model} (keep_alive={keep_alive})...")
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": keep_alive,
            "options": {
                "temperature": temperature,
                "num_predict": 1000
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Ollama: [SUCCESS] Task completed by {model}")
            return response.json().get("response", "").strip()

    async def unload_model(self, model: str):
        """Explicitly unloads a model from RAM."""
        logger.info(f"Ollama: [RAM OPTIMIZATION] Requesting UNLOAD for model: {model}")
        url = f"{self.ollama_host.rstrip('/')}/api/generate"
        
        if "localhost" in url or "127.0.0.1" in url:
            import os
            if os.path.exists("/.dockerenv"):
                url = url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")

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
            sql = f'SHOW CREATE TABLE "{schema_name}"."{table_name}"'
            result = duckdb_manager.connection.execute(sql).fetchone()
            if result:
                return result[0]
            return f"Table {table_name} exists but schema could not be retrieved."
        except Exception as e:
            logger.error(f"Error getting schema for {table_name}: {e}")
            return f"Error retrieving schema for {table_name}."

    async def generate_sql(self, question: str, table_name: str, schema_name: str = "main") -> Optional[str]:
        """Generates SQL using duckdb-nsql."""
        schema = self._get_schema(table_name, schema_name)
        
        prompt = f"""### Instruction:
Your query should be compatible with DuckDB. Use the provided schema.
### Schema:
{schema}
### Question:
{question}
### Response (use duckdb):
"""
        try:
            # RAM Swap: Unload persona model before loading SQL brain
            await self.unload_model(self.model_persona)
            
            # Generate SQL with immediate unload
            logger.info("Ollama: [BRAIN] Generating surgical SQL via duckdb-nsql...")
            response = await self._generate(prompt, self.model_sql, keep_alive=0)
            
            # Extract SQL from potential markdown or prefixes
            sql = response.strip()
            if "```sql" in sql:
                sql = re.search(r"```sql\s*(.*?)\s*```", sql, re.DOTALL).group(1)
            elif "```" in sql:
                sql = re.search(r"```\s*(.*?)\s*```", sql, re.DOTALL).group(1)
            
            sql = sql.replace("SELECT", "SELECT").strip("; ")
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
            # Load Persona model for formatting/decision
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
            
            # AI Passione Palette (Premium Neons/Teals)
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
            return {"type": "error", "message": f"Visualization failed: {str(e)}"}

    async def process_question(self, question: str, table_name: str, schema_name: str = "main") -> Dict[str, Any]:
        """High-level entry point to process a question and get either text or viz."""
        prompt = f"""Is this a question that requires a data visualization (chart, plot, graph)? 
Question: "{question}"
Respond ONLY with 'YES' or 'NO'."""
        
        logger.info(f"Ollama: [ANALYSIS] Analyzing Operator query: '{question}'")
        decision = await self._generate(prompt, self.model_persona)
        
        if "YES" in decision.upper():
            logger.info("Ollama: [ANALYSIS] Visualization required. Engaging SQL Brain.")
            sql = await self.generate_sql(question, table_name, schema_name)
            if sql:
                viz_payload = await self.create_viz_payload(sql, question)
                return {
                    "answer_type": "viz",
                    "sql": sql,
                    "viz": viz_payload
                }
        
        logger.info("Ollama: [ANALYSIS] Standard textual response sufficient.")
        return {"answer_type": "text"}
