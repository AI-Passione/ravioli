import json
import logging
import re
import httpx
import os
import pandas as pd
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from pydantic import BaseModel, Field
from ravioli.backend.core.config import settings
from ravioli.backend.data.olap.duckdb_manager import duckdb_manager
from ravioli.backend.core.models import SystemSetting
from ravioli.backend.core.encryption import decrypt_value

# LangChain Imports
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

logger = logging.getLogger(__name__)

class VizStrategy(BaseModel):
    """Structured output for chart configuration."""
    chart_type: str = Field(description="The type of chart: 'bar', 'line', 'pie', or 'scatter'")
    labels_column: str = Field(description="The column name to use for the X-axis labels")
    values_columns: List[str] = Field(description="List of column names to use for the Y-axis values")
    title: str = Field(description="A clinical title for the chart")

class AnalysisDecision(BaseModel):
    """Decision on whether visualization is needed."""
    requires_viz: bool = Field(description="Whether the question requires a data visualization")

class KowalskiSQLAgent:
    """
    A surgical SQL agent for Kowalski.
    Uses OllamaLLM (LangChain) for consistent /api/generate behavior.
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self._config = self._load_config()
        self.model_sql = "duckdb-nsql"
        self.model_persona = "gemma3:4b"
        
        # Diagnostic logging
        mode = self.mode
        has_key = bool(self.api_key)
        logger.info(f"KowalskiSQLAgent: Initialized in {mode} mode. API Key present: {has_key}")

    def _load_config(self) -> Dict[str, Any]:
        """Load Ollama configuration from the database."""
        if self.db_session:
            try:
                setting = self.db_session.query(SystemSetting).filter(SystemSetting.key == "ollama").first()
                if setting and setting.value:
                    config = dict(setting.value)
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
        if "localhost" in url or "127.0.0.1" in url or "ollama" in url:
            if os.path.exists("/.dockerenv"):
                return url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal").replace("ollama", "host.docker.internal")
        return url

    def _get_llm(self, model: str, temperature: float = 0.1, keep_alive: Any = "5m"):
        """Creates a LangChain OllamaLLM instance."""
        headers = {}
        if self.mode == "cloud" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return OllamaLLM(
            model=model,
            base_url=self.ollama_host,
            temperature=temperature,
            keep_alive=keep_alive if self.mode != "cloud" else "5m",
            headers=headers
        )

    async def _generate(self, prompt_text: str, model: str, temperature: float = 0.1, keep_alive: Any = "5m", parser: Any = None) -> Union[str, Dict]:
        """Internal helper for LLM generation."""
        llm = self._get_llm(model, temperature=temperature, keep_alive=keep_alive)
        if parser:
            chain = llm | parser
        else:
            chain = llm | StrOutputParser()
        
        try:
            return await chain.ainvoke(prompt_text)
        except Exception as e:
            if "401" in str(e) or "unauthorized" in str(e).lower():
                logger.error(f"KowalskiSQLAgent: Authentication failed for {self.ollama_host}. Mode: {self.mode}")
                raise Exception("Ollama Cloud authentication failed. Please verify your API key in Settings.")
            raise e

    async def unload_model(self, model: str):
        """Explicitly unloads a model from RAM."""
        if self.mode == "cloud": return
        logger.info(f"Ollama: [RAM OPTIMIZATION] Requesting UNLOAD for model: {model}")
        url = f"{self.ollama_host.rstrip('/')}/api/generate"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json={"model": model, "keep_alive": 0})
            logger.info(f"Ollama: [RAM OPTIMIZATION] {model} has been evicted.")
        except Exception as e:
            logger.warning(f"Ollama: [RAM OPTIMIZATION] Unload failed: {e}")

    def _get_schema(self, table_name: str, schema_name: str = "main") -> str:
        """Extracts table schema for context."""
        try:
            sql = "SELECT sql FROM duckdb_tables WHERE schema_name = ? AND table_name = ?"
            result = duckdb_manager.connection.execute(sql, [schema_name, table_name]).fetchone()
            if result and result[0]: return result[0]
            cols = duckdb_manager.connection.execute(f'DESCRIBE "{schema_name}"."{table_name}"').fetchall()
            return f"Table {table_name} columns: {', '.join([c[0] for c in cols])}"
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return "Error retrieving schema."

    async def generate_sql(self, question: str, table_name: str, schema_name: str = "main") -> Optional[str]:
        """Generates SQL with aggressive cleaning."""
        schema = self._get_schema(table_name, schema_name)
        prompt = PromptTemplate.from_template("""### Instruction:
Your query should be compatible with DuckDB. Use the provided schema.
### Schema:
{schema}
### Question:
{question}
### Response (use duckdb):
""")
        
        target_model = self.model_sql if self.mode != "cloud" else self._config.get("default_model", self.model_persona)

        try:
            if self.mode != "cloud": await self.unload_model(self.model_persona)
            logger.info(f"Ollama: [BRAIN] Generating surgical SQL via {target_model}...")
            
            response = await self._generate(
                prompt.format(schema=schema, question=question),
                target_model,
                keep_alive=0 if self.mode != "cloud" else "5m"
            )
            
            sql = response.strip()
            if "```" in sql:
                match = re.search(r"```(?:sql)?\s*(.*?)\s*```", sql, re.DOTALL)
                if match: sql = match.group(1).strip()
            
            keywords = r"(SELECT|WITH|SHOW|DESCRIBE|CREATE|DROP|INSERT|UPDATE|DELETE|ALTER)"
            match = re.search(rf"({keywords}\s+.*)", sql, re.IGNORECASE | re.DOTALL)
            if match: sql = match.group(1).strip()
            
            for kw in ["SELECT", "WITH", "SHOW"]:
                idx = sql.upper().find(kw)
                if idx != -1: 
                    sql = sql[idx:].strip()
                    break

            sql = sql.split(';')[0].strip()
            logger.info(f"Ollama: [BRAIN] SQL Final: {sql}")
            return sql
        except Exception as e:
            logger.error(f"SQL Generation failed: {e}")
            return None

    async def create_viz_payload(self, sql: str, original_question: str) -> Dict[str, Any]:
        """Uses JsonOutputParser for robust strategy assembly."""
        try:
            logger.info("Ollama: [VOICE] Kowalski is analyzing query results...")
            df = duckdb_manager.connection.execute(sql).fetchdf()
            if df.empty: return {"type": "error", "message": "Query returned no data."}

            for col in df.select_dtypes(include=['datetime64', 'datetimetz']).columns:
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            parser = JsonOutputParser(pydantic_object=VizStrategy)
            prompt = PromptTemplate.from_template("""You are Kowalski, a data visualization expert.
Question: "{question}"
Columns: {columns}
Sample Data: {sample_data}

{format_instructions}
""")
            
            config = await self._generate(
                prompt.format(
                    question=original_question,
                    columns=df.columns.tolist(),
                    sample_data=json.dumps(df.head(5).to_dict(orient='records')),
                    format_instructions=parser.get_format_instructions()
                ),
                self.model_persona,
                temperature=0.1,
                parser=parser
            )

            datasets = []
            colors = ["rgba(0, 245, 212, 0.6)", "rgba(18, 113, 255, 0.6)", "rgba(157, 78, 221, 0.6)", "rgba(255, 0, 110, 0.6)"]
            border_colors = ["rgba(0, 245, 212, 1)", "rgba(18, 113, 255, 1)", "rgba(157, 78, 221, 1)", "rgba(255, 0, 110, 1)"]

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

            logger.info(f"Ollama: [VOICE] Visualization strategy locked: {config['chart_type']}")
            return {
                "type": "chart",
                "chart_type": config["chart_type"],
                "title": config["title"],
                "data": {"labels": df[config["labels_column"]].tolist(), "datasets": datasets}
            }
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
            return {"type": "error", "message": str(e)}

    async def process_question(self, question: str, table_name: str, schema_name: str = "main") -> AsyncGenerator[Any, None]:
        """Decision engine using JsonOutputParser."""
        parser = JsonOutputParser(pydantic_object=AnalysisDecision)
        prompt = PromptTemplate.from_template("""Does this question require a chart or graph to answer?
Question: "{question}"
{format_instructions}
""")
        
        logger.info(f"Ollama: [ANALYSIS] Analyzing Operator query: '{question}'")
        try:
            result = await self._generate(
                prompt.format(question=question, format_instructions=parser.get_format_instructions()),
                self.model_persona,
                parser=parser
            )
            
            if result.get("requires_viz"):
                yield "_[Kowalski is engaging the Statistical Brain for visualization...]_"
                yield "_[Generating surgical SQL query...]_"
                sql = await self.generate_sql(question, table_name, schema_name)
                
                if sql:
                    yield f"_[Executing query and assembling vision strategy...]_"
                    viz_payload = await self.create_viz_payload(sql, question)
                    
                    if viz_payload.get("type") == "error":
                        yield f"> [!WARNING]\n> **Visualization Bypass**: {viz_payload.get('message')}\n\nFalling back to textual analysis."
                    else:
                        yield {"answer_type": "viz", "sql": sql, "viz": viz_payload}
                        return
                else:
                    yield f"> [!WARNING]\n> **Neural Synthesis Failed**: Valid query could not be constructed."
            
            yield {"answer_type": "text"}
        except Exception as e:
            logger.error(f"Process question failed: {e}")
            yield f"> [!ERROR]\n> **Neural Link Failed**: {str(e)}"
            yield {"answer_type": "text", "error": str(e)}
