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
    Uses duckdb-nsql to generate DuckDB-compatible SQL from natural language.
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.ollama_host = settings.ollama_host
        self.model_sql = "duckdb-nsql"
        self.model_persona = "gemma3:4b"

    async def _generate(self, prompt: str, model: str, temperature: float = 0.1) -> str:
        url = f"{self.ollama_host.rstrip('/')}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 1000
            }
        }
        
        # Handle Docker-to-Host communication for Ollama
        if "localhost" in url or "127.0.0.1" in url:
            import os
            if os.path.exists("/.dockerenv"):
                url = url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "").strip()

    def _get_schema(self, table_name: str, schema_name: str = "main") -> str:
        """Extracts the CREATE TABLE statement for context."""
        try:
            # DuckDB specific way to get schema
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
            response = await self._generate(prompt, self.model_sql)
            # Extract SQL from potential markdown or prefixes
            sql = response.strip()
            if "```sql" in sql:
                sql = re.search(r"```sql\s*(.*?)\s*```", sql, re.DOTALL).group(1)
            elif "```" in sql:
                sql = re.search(r"```\s*(.*?)\s*```", sql, re.DOTALL).group(1)
            
            # Clean up trailing semicolons or prefix words
            sql = sql.replace("SELECT", "SELECT").strip("; ")
            return sql
        except Exception as e:
            logger.error(f"SQL Generation failed: {e}")
            return None

    async def create_viz_payload(self, sql: str, original_question: str) -> Dict[str, Any]:
        """
        Executes SQL and uses LLM to decide on best chart type and formatting.
        """
        try:
            df = duckdb_manager.connection.execute(sql).fetchdf()
            if df.empty:
                return {"type": "error", "message": "Query returned no data."}

            # Convert types for JSON serialization
            for col in df.select_dtypes(include=['datetime64', 'datetimetz']).columns:
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            data_sample = df.head(5).to_dict(orient='records')
            columns = df.columns.tolist()

            # Ask gemma3 to decide on the best chart type
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
                # Fallback to simple bar chart
                config = {
                    "chart_type": "bar",
                    "labels_column": columns[0],
                    "values_columns": [columns[1]] if len(columns) > 1 else [],
                    "title": "Data Visualization"
                }
            else:
                config = json.loads(match.group(0))

            # Build the Chart.js compatible payload
            labels = df[config["labels_column"]].tolist()
            datasets = []
            
            # AI Passione Palette
            colors = [
                "rgba(0, 150, 136, 0.8)",  # Teal
                "rgba(33, 150, 243, 0.8)",  # Blue
                "rgba(156, 39, 176, 0.8)",  # Purple
                "rgba(255, 152, 0, 0.8)",   # Orange
            ]

            for i, col in enumerate(config["values_columns"]):
                datasets.append({
                    "label": col,
                    "data": df[col].tolist(),
                    "backgroundColor": colors[i % len(colors)],
                    "borderColor": colors[i % len(colors)].replace("0.8", "1.0"),
                    "borderWidth": 1
                })

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
        # 1. Decide if it's a visualization question
        prompt = f"""Is this a question that requires a data visualization (chart, plot, graph)? 
Question: "{question}"
Respond ONLY with 'YES' or 'NO'."""
        
        decision = await self._generate(prompt, self.model_persona)
        
        if "YES" in decision.upper():
            sql = await self.generate_sql(question, table_name, schema_name)
            if sql:
                viz_payload = await self.create_viz_payload(sql, question)
                return {
                    "answer_type": "viz",
                    "sql": sql,
                    "viz": viz_payload
                }
        
        return {"answer_type": "text"}
