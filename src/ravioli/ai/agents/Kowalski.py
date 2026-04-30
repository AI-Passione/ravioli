import logging
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, AsyncGenerator, Union, List
from pydantic import BaseModel, Field

# LangChain Imports
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.agents import initialize_agent, AgentType
from langchain_community.utilities import SQLDatabase
from langchain_community.llms import Ollama

# Core Imports
from ravioli.backend.core.config import settings
from ravioli.backend.core.ollama import OllamaClient

# Tools Imports
from ravioli.ai.tools.sql import create_sql_agent_executor, get_query_database_tool
from ravioli.ai.tools.operations import ingest_data_tool, run_transformations_tool
from ravioli.ai.tools import generate_sql as tool_generate_sql
from ravioli.ai.tools import create_viz_payload as tool_create_viz_payload

logger = logging.getLogger(__name__)

class AnalysisDecision(BaseModel):
    """Decision on whether visualization is needed."""
    requires_viz: bool = Field(description="Whether the question requires a data visualization")

class KowalskiAgent:
    """
    The Unified Intelligence entry point for Kowalski.
    Acts as an orchestrator for various specialized skills (analysis, communication, etc.)
    """
    def __init__(self, db_session=None, model_name: str = "qwen2.5:3b"):
        self.db_session = db_session
        self.model_name = model_name
        self.ollama_client = OllamaClient(db_session)
        self.model_sql = "duckdb-nsql"
        self.model_persona = "gemma3:4b"
        self.persona = self._load_persona()
        self.llm = Ollama(model=model_name)
        self.agent = self._setup_agent()
        logger.info(f"KowalskiAgent: Unified intelligence initialized.")

    def _load_persona(self) -> str:
        """Loads Kowalski's soul and skills from the local filesystem."""
        persona = "You are Kowalski, a lead analytics specialist. Clinical and precise."
        skills = ""
        try:
            base_ai_path = Path(__file__).resolve().parents[1]
            persona_path = base_ai_path / "agents" / "soul.md"
            if persona_path.exists(): persona = persona_path.read_text()
            skills_path = base_ai_path / "skills" / "skills.md"
            if skills_path.exists(): skills = skills_path.read_text()
        except Exception as e:
            logger.warning(f"KowalskiAgent: [WARNING] Failed to load dossier/skills: {e}")
        return f"{persona}\n\n## SPECIALIZED SKILLS\n{skills}" if skills else persona

    async def generate(self, prompt_text: str, task_name: str, temperature: float = 0.1, parser: Any = None) -> Union[str, Dict]:
        """Internal helper for persona-injected generation."""
        try:
            full_prompt = f"{self.persona}\n\nTask: {prompt_text}"
            response_text = await self.ollama_client.generate(
                prompt=full_prompt,
                task_name=task_name,
                temperature=temperature,
                num_predict=1000
            )
            if parser: return parser.parse(response_text)
            return response_text
        except Exception as e:
            logger.error(f"KowalskiAgent: LLM Generation failed ({task_name}): {e}")
            raise e

    # --- Intelligence Orchestration ---

    async def generate_sql(self, question: str, table_name: str, schema_name: str = "main") -> Optional[str]:
        target_model = self.ollama_client.model if self.ollama_client.mode != "cloud" else self.ollama_client.model
        return await tool_generate_sql(question, table_name, self.generate, target_model, schema_name)

    async def create_viz_payload(self, sql: str, original_question: str) -> Dict[str, Any]:
        return await tool_create_viz_payload(sql, original_question, self.generate, self.model_persona)

    async def process_question(self, question: str, table_name: str, schema_name: str = "main") -> AsyncGenerator[Any, None]:
        parser = JsonOutputParser(pydantic_object=AnalysisDecision)
        prompt = PromptTemplate.from_template("Does this require a chart?\nQuestion: \"{question}\"\n{format_instructions}")
        try:
            result = await self.generate(prompt.format(question=question, format_instructions=parser.get_format_instructions()), "Decision", parser=parser)
            if result.get("requires_viz"):
                yield "_[Engaging Statistical Brain...]_"
                sql = await self.generate_sql(question, table_name, schema_name)
                if sql:
                    yield f"_[Assembling vision strategy...]_"
                    viz = await self.create_viz_payload(sql, question)
                    yield {"answer_type": "viz", "sql": sql, "viz": viz}
                    return
            yield {"answer_type": "text"}
        except Exception:
            yield {"answer_type": "text"}

    # --- Infrastructure ---

    async def check_ollama_connection(self):
        return await self.ollama_client.check_connection()

    def _setup_agent(self):
        schemas = "public,marts,s_spotify,s_linkedin,s_substack,s_telegram,s_bolt,s_apple_health,s_google_sheet"
        db_uri = f"{settings.database_url}?options=-csearch_path%3D{schemas}"
        db = SQLDatabase.from_uri(db_uri)
        sql_executor = create_sql_agent_executor(db=db, llm=self.llm, persona=self.persona)
        query_tool = get_query_database_tool(sql_executor)
        tools = [ingest_data_tool, run_transformations_tool, query_tool]
        return initialize_agent(tools, self.llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True, max_iterations=10)

    def chat(self, prompt: str):
        try:
            response = self.agent.invoke({"input": prompt})
            return response.get('output', str(response)) if isinstance(response, dict) else str(response)
        except Exception as e: return f"Error: {e}"

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str)
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    agent = KowalskiAgent()
    if not await agent.check_ollama_connection(): return
    if args.interactive:
        while True:
            u = input(">> ")
            if u.lower() in ["exit", "quit"]: break
            print(agent.chat(u))
    elif args.prompt: print(agent.chat(args.prompt))

if __name__ == "__main__":
    asyncio.run(main())
