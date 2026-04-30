import logging
import re
from typing import Optional, Any
from langchain_core.prompts import PromptTemplate
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain.agents import AgentType
from langchain.tools import Tool as LangChainTool
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

def clean_sql_query(query: str) -> str:
    """Helper to clean SQL from the agent."""
    query = query.strip()
    # Remove markdown code blocks if present
    if "```" in query:
        match = re.search(r"```(?:sql)?\s*(.*?)\s*```", query, re.DOTALL | re.IGNORECASE)
        if match:
            query = match.group(1)
        else:
            query = query.replace("```sql", "").replace("```", "")
    
    # Remove leading "sql" if the model adds it outside backticks
    if query.lower().startswith("sql"):
        query = query[3:].strip()
        
    return query.strip("` \n\t;")

def create_sql_agent_executor(db, llm, persona: str):
    """Creates an SQL agent for querying the database."""
    # Custom error handler for parsing errors
    def handle_parsing_error(error) -> str:
        error_str = str(error)
        if "SELECT" in error_str or "Action:" in error_str:
            return f"I had a parsing error. I will try to be more concise. Error: {error_str[:50]}"
        return f"I encountered an issue. Let me try a simpler approach. Error: {error_str[:100]}"

    # Custom prefix to teach the agent about the data warehouse schema structure
    sql_prefix = f"""{persona}
    
You are an agent designed to interact with a SQL database.
All relevant schemas (marts, s_*) are in your search path.

DATA CATEGORIZATION:
1. RAW DATA: Located in `s_` schemas (e.g., s_substack, s_linkedin). This is the landing zone for the ingestion system.
2. CURATED DATA: Located in the `marts` schema. This is cleaned, modeled data ready for insight generation and analysis.

CRITICAL SCHEMA PRIORITIES:
1. MART SYSTEM: Use the `marts` schema for all analytical questions and insights. This is your primary source of truth.
2. INGESTION SYSTEM: Use the `s_` schemas only when asked for "raw data" or when debugging ingestion.
3. IGNORE: Do NOT use or refer to the `staging` or `intermediate` schemas.

CRITICAL RULES:
1. When asked "what data is there" or to "check data", you MUST list tables from both `marts` and `s_` schemas. 
2. Explicitly label tables as "Raw Data" or "Curated/Ready for Insights".
3. SOURCE ATTRIBUTION: For "Raw Data", identify the source application based on the schema (e.g., `s_linkedin` is LinkedIn, `s_spotify` is Spotify, `s_substack` is Substack, `s_bolt` is Bolt, `s_apple_health` is Apple Health). Tell the user which app generated the data.
4. HALLUCINATION PREVENTION: If a schema (e.g., `marts`) is empty or `sql_db_list_tables` returns nothing, state clearly that no data is available. DO NOT invent information.
5. RESPONSE FORMAT: Always provide a concise **Executive Summary** followed by **Bullet Points**.
6. NEVER include markdown backticks (```) or the word "sql" in your tool inputs. Only provide raw SQL.
7. PUBLIC SCHEMA IS EMPTY. Do NOT query `information_schema` filtering for `table_schema = 'public'`.

WORKFLOW:
1. Use `sql_db_list_tables` to see available tables.
2. Categorize them into Raw (s_*) and Curated (marts).
3. Tell the user what raw data is available and what curated data is ready for insight generation.
4. Execute queries on `marts` for insights.
"""

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    original_tools = toolkit.get_tools()
    cleaned_tools = []
    
    for t in original_tools:
        if t.name == "sql_db_query":
            # Create a wrapper that cleans the SQL before calling the original tool
            def wrapped_query(query: str, tool=t):
                cleaned = clean_sql_query(query)
                return tool.run(cleaned)
            
            # Create a new Tool with the same metadata but our wrapped function
            new_tool = LangChainTool(
                name=t.name,
                description=t.description,
                func=wrapped_query
            )
            cleaned_tools.append(new_tool)
        else:
            cleaned_tools.append(t)

    return create_sql_agent(
        llm=llm,
        toolkit=None,  # Pass tools directly
        tools=cleaned_tools,
        db=db,
        verbose=True,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=handle_parsing_error,
        prefix=sql_prefix,
        max_iterations=10,
        max_execution_time=60,
    )
