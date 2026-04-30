
import os
import sys
import argparse
from typing import Optional

import os
import sys
import argparse
from typing import Optional

from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.tools import tool
from langchain_community.utilities import SQLDatabase

from ravioli.backend.core.config import settings
from ravioli.ai.tools.sql import create_sql_agent_executor
from ravioli.ai.tools.operations import ingest_data_tool, run_transformations_tool


class KowalskiAgent:
    def __init__(self, model_name: str = "qwen2.5:3b"):
        self.model_name = model_name
        self.llm = Ollama(model=model_name)
        self.persona = self._load_persona()
        self.agent = self._setup_agent()

    def _load_persona(self) -> str:
        """Loads Kowalski's soul and skills."""
        from pathlib import Path
        try:
            # Relative to src/ravioli/ai/agents/ravioli_agent.py
            # parents[1] is src/ravioli/ai/
            base_path = Path(__file__).resolve().parents[1]
            soul = (base_path / "agents" / "soul.md").read_text()
            skills = (base_path / "skills" / "skills.md").read_text()
            return f"{soul}\n\n## SPECIALIZED SKILLS\n{skills}"
        except Exception:
            return "You are Kowalski, a clinical data analyst."

    def check_ollama_connection(self):
        """Checks if Ollama is reachable."""
        try:
            import requests
            response = requests.get("http://localhost:11434")
            if response.status_code == 200:
                return True
        except Exception:
            pass
        return False

    def _get_sql_agent(self, db):
        """Creates an SQL agent for querying the database."""
        return create_sql_agent_executor(db=db, llm=self.llm, persona=self.persona)

    def _setup_agent(self):
        # Define the schemas we want to include in our search path (Focusing only on what matters)
        schemas = "public,marts,s_spotify,s_linkedin,s_substack,s_telegram,s_bolt,s_apple_health,s_google_sheet"
        
        # Update URI to include search_path
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

        tools = [
            ingest_data_tool,
            run_transformations_tool,
            query_database_tool
        ]

        # Custom error handler for the main agent
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
        """Sends a message to the agent and returns the response.
        
        Args:
            prompt: The user's question/prompt
            callbacks: Optional list of LangChain callbacks for streaming output
            
        Returns:
            tuple: (response_text, intermediate_steps) if callbacks provided, else just response_text
        """
        try:
            config = {"callbacks": callbacks} if callbacks else {}
            response = self.agent.invoke({"input": prompt}, config=config)
            
            # Return both output and intermediate steps if available
            if isinstance(response, dict):
                output = response.get('output', str(response))
                intermediate_steps = response.get('intermediate_steps', [])
                return output if not callbacks else (output, intermediate_steps)
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
