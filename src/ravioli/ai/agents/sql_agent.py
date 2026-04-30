import logging
from typing import Dict, Any, Optional, AsyncGenerator, Union
from pydantic import BaseModel, Field
from ravioli.backend.core.ollama import OllamaClient, KOWALSKI_PERSONA

# LangChain Imports
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Tools Imports
from ravioli.ai.tools import generate_sql as tool_generate_sql
from ravioli.ai.tools import create_viz_payload as tool_create_viz_payload

logger = logging.getLogger(__name__)

class AnalysisDecision(BaseModel):
    """Decision on whether visualization is needed."""
    requires_viz: bool = Field(description="Whether the question requires a data visualization")

class KowalskiSQLAgent:
    """
    A surgical SQL agent for Kowalski.
    Uses the system's proven OllamaClient for robust LLM communication.
    Integrates with LangChain for structured reasoning and parsing.
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        # Leverage the proven OllamaClient directly
        self._ollama_client = OllamaClient(db_session)
        self.model_sql = "duckdb-nsql"
        self.model_persona = "gemma3:4b"
        logger.info(f"KowalskiSQLAgent: Initialized with direct OllamaClient integration. Mode: {self._ollama_client.mode}")

    async def _generate(self, prompt_text: str, task_name: str, model: str, temperature: float = 0.1, parser: Any = None) -> Union[str, Dict]:
        """
        Internal helper that routes to the proven OllamaClient._generate.
        Supports LangChain parsers for structured output.
        """
        try:
            # Inject Kowalski's persona and specialized skills into every request
            full_prompt = f"{KOWALSKI_PERSONA}\n\nTask: {prompt_text}"
            
            # Call the battle-tested _generate from ollama.py
            response_text = await self._ollama_client._generate(
                prompt=full_prompt,
                task_name=task_name,
                model=model,
                temperature=temperature,
                num_predict=1000
            )
            
            if parser:
                # Use LangChain parser to transform the raw text
                return parser.parse(response_text)
            
            return response_text
        except Exception as e:
            logger.error(f"KowalskiSQLAgent: LLM Generation failed ({task_name}): {e}")
            raise e

    async def unload_model(self, model: str):
        """Explicitly unloads a model from RAM via OllamaClient."""
        if self._ollama_client.mode == "cloud": return
        await self._ollama_client.unload_model(model)

    async def generate_sql(self, question: str, table_name: str, schema_name: str = "main") -> Optional[str]:
        """Generates SQL with aggressive cleaning using specialized tools."""
        target_model = self.model_sql if self._ollama_client.mode != "cloud" else self._ollama_client.model
        try:
            if self._ollama_client.mode != "cloud": 
                await self.unload_model(self.model_persona)
            
            return await tool_generate_sql(
                question=question,
                table_name=table_name,
                generate_fn=self._generate,
                model=target_model,
                schema_name=schema_name
            )
        except Exception as e:
            logger.error(f"SQL Generation failed: {e}")
            return None

    async def create_viz_payload(self, sql: str, original_question: str) -> Dict[str, Any]:
        """Uses visualization tool for robust strategy assembly."""
        return await tool_create_viz_payload(
            sql=sql,
            original_question=original_question,
            generate_fn=self._generate,
            model=self.model_persona
        )

    async def process_question(self, question: str, table_name: str, schema_name: str = "main") -> AsyncGenerator[Any, None]:
        """Decision engine using JsonOutputParser and OllamaClient."""
        parser = JsonOutputParser(pydantic_object=AnalysisDecision)
        prompt = PromptTemplate.from_template("""Does this question require a chart or graph to answer?
Question: "{question}"
{format_instructions}
""")
        logger.info(f"Ollama: [ANALYSIS] Analyzing Operator query: '{question}'")
        try:
            result = await self._generate(
                prompt_text=prompt.format(question=question, format_instructions=parser.get_format_instructions()),
                task_name="Decision Analysis",
                model=self.model_persona,
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
