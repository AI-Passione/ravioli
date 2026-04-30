import logging
from typing import Dict, Any, Optional, AsyncGenerator, Union, List
from pydantic import BaseModel, Field

# LangChain Imports
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_community.llms import Ollama

# Core Imports
from ravioli.backend.core.config import settings
from ravioli.backend.core.ollama import OllamaClient, KOWALSKI_PERSONA

# Tools Imports
from ravioli.ai.tools.sql import create_sql_agent_executor
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
    Combines surgical SQL generation with a general-purpose ReAct agent.
    """
    def __init__(self, db_session=None, model_name: str = "qwen2.5:3b"):
        self.db_session = db_session
        self.model_name = model_name
        # Leverage the proven OllamaClient directly
        self._ollama_client = OllamaClient(db_session)
        self.model_sql = "duckdb-nsql"
        self.model_persona = "gemma3:4b"
        self.persona = KOWALSKI_PERSONA
        self.llm = Ollama(model=model_name) # For the ReAct agent
        self.agent = self._setup_agent()
        logger.info(f"KowalskiAgent: Unified intelligence initialized. Mode: {self._ollama_client.mode}")

    async def _generate(self, prompt_text: str, task_name: str, model: str, temperature: float = 0.1, parser: Any = None) -> Union[str, Dict]:
        """Internal helper that routes to the proven OllamaClient._generate with persona injection."""
        try:
            # Inject Kowalski's persona and specialized skills into every request
            full_prompt = f"{self.persona}\n\nTask: {prompt_text}"
            
            response_text = await self._ollama_client._generate(
                prompt=full_prompt,
                task_name=task_name,
                model=model,
                temperature=temperature,
                num_predict=1000
            )
            
            if parser:
                return parser.parse(response_text)
            return response_text
        except Exception as e:
            logger.error(f"KowalskiAgent: LLM Generation failed ({task_name}): {e}")
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
        """Surgical decision engine for streaming backend responses."""
        parser = JsonOutputParser(pydantic_object=AnalysisDecision)
        prompt = PromptTemplate.from_template("""Does this question require a chart or graph to answer?
Question: "{question}"
{format_instructions}
""")
        logger.info(f"Ollama: [ANALYSIS] Kowalski is analyzing Operator query: '{question}'")
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

    def check_ollama_connection(self):
        """Checks if Ollama is reachable."""
        import httpx
        try:
            url = f"{self._ollama_client.base_url.rstrip('/')}/api/tags"
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    def _get_sql_agent(self, db):
        """Creates an SQL agent for the ReAct loop."""
        return create_sql_agent_executor(db=db, llm=self.llm, persona=self.persona)

    def _setup_agent(self):
        # Define the schemas we want to include in our search path
        schemas = "public,marts,s_spotify,s_linkedin,s_substack,s_telegram,s_bolt,s_apple_health,s_google_sheet"
        db_uri = f"{settings.database_url}?options=-csearch_path%3D{schemas}"
        db = SQLDatabase.from_uri(db_uri)

        sql_agent_executor = self._get_sql_agent(db)

        @tool
        def query_database_tool(query_description: str):
            """Useful for when you need to answer questions about data in the Data Warehouse. 
            Input should be a natural language question about the data."""
            try:
                result = sql_agent_executor.invoke({"input": query_description})
                if isinstance(result, dict):
                    return result.get("output", str(result))
                return str(result)
            except Exception as e:
                return f"Error querying database: {str(e)}"

        tools = [ingest_data_tool, run_transformations_tool, query_database_tool]

        def handle_main_agent_error(error) -> str:
            return f"I had trouble processing that. Let me try again with a simpler approach."

        return initialize_agent(
            tools, 
            self.llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True,
            handle_parsing_errors=handle_main_agent_error,
            max_iterations=10,
            max_execution_time=120,
        )

    def chat(self, prompt: str, callbacks=None):
        """Sends a message to the ReAct agent."""
        try:
            config = {"callbacks": callbacks} if callbacks else {}
            response = self.agent.invoke({"input": prompt}, config=config)
            if isinstance(response, dict):
                output = response.get('output', str(response))
                return output
            return str(response)
        except Exception as e:
            return f"Error: {e}"

def main():
    parser = argparse.ArgumentParser(description="Ravioli AI Client")
    parser.add_argument("--prompt", type=str, help="The prompt to send to the AI")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--model", type=str, default="qwen2.5:3b", help="Ollama model to use")
    
    args = parser.parse_args()
    
    agent = KowalskiAgent(model_name=args.model)

    if not agent.check_ollama_connection():
        print("\n\033[91mError: Could not connect to Ollama.\033[0m")
        print("Please ensure Ollama is running by executing: \033[1mollama serve\033[0m")
        print("Keep that terminal open and run this agent in a new terminal.\n")
        return

    if args.interactive:
        print(f"Ravioli AI Client ({args.model}) (Type 'exit' to quit)")
        while True:
            user_input = input(">> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            print(agent.chat(user_input))
    
    elif args.prompt:
        print(agent.chat(args.prompt))
    else:
        print("Please provide a prompt using --prompt or run with --interactive")

if __name__ == "__main__":
    main()
