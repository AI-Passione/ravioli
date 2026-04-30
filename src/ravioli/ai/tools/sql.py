import logging
import re
from typing import Optional, Any
from langchain_core.prompts import PromptTemplate
from ravioli.backend.data.olap.duckdb_manager import duckdb_manager

logger = logging.getLogger(__name__)

def get_schema(table_name: str, schema_name: str = "main") -> str:
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

async def generate_sql(
    question: str, 
    table_name: str, 
    generate_fn: Any,
    model: str,
    schema_name: str = "main"
) -> Optional[str]:
    """Generates SQL with aggressive cleaning."""
    schema = get_schema(table_name, schema_name)
    prompt = PromptTemplate.from_template("""### Instruction:
Your query should be compatible with DuckDB. Use the provided schema.
### Schema:
{schema}
### Question:
{question}
### Response (use duckdb):
""")
    
    try:
        logger.info(f"Ollama: [BRAIN] Generating surgical SQL via {model}...")
        
        response = await generate_fn(
            prompt_text=prompt.format(schema=schema, question=question),
            task_name="SQL Generation",
            model=model
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
