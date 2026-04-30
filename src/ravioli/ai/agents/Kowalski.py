import logging
import json
import re
import time
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
    Combines surgical SQL generation, data analysis, and general-purpose ReAct orchestration.
    """
    def __init__(self, db_session=None, model_name: str = "qwen2.5:3b"):
        self.db_session = db_session
        self.model_name = model_name
        self._ollama_client = OllamaClient(db_session)
        self.model_sql = "duckdb-nsql"
        self.model_persona = "gemma3:4b"
        self.persona = self._load_persona()
        self.llm = Ollama(model=model_name)
        self.agent = self._setup_agent()
        logger.info(f"KowalskiAgent: Unified intelligence initialized.")

    def _load_persona(self) -> str:
        """Loads Kowalski's soul and skills from the local filesystem."""
        from pathlib import Path
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

    async def _generate(self, prompt_text: str, task_name: str, model: str = None, temperature: float = 0.1, parser: Any = None) -> Union[str, Dict]:
        """Internal helper for persona-injected generation."""
        try:
            full_prompt = f"{self.persona}\n\nTask: {prompt_text}"
            response_text = await self._ollama_client.generate(
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

    # --- Analytical Skills ---

    async def analyze_sheet_structure(self, sheet_name: str, sample_grid: str) -> Dict[str, Any]:
        """Methodically analyze Excel sheet structure for ingestion."""
        prompt = f"""Task: Methodically analyze the structural integrity and layout of Excel sheet "{sheet_name}".
Context: You are inspecting a VISUAL GRID of the first 20 rows of an Excel sheet. 
Criteria for JSON: verdict ("ready", "needs_fix", "split_table", "reject"), header_row, data_start_row, is_split, column_mapping.
Grid:
{sample_grid}
Return ONLY clinical JSON."""
        try:
            content = await self._generate(prompt, "Structural Analysis", temperature=0.1)
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match: return json.loads(match.group(0))
            return {"verdict": "reject", "reason": "Parse failure"}
        except Exception:
            return {"verdict": "ready", "header_row": 0, "data_start_row": 1, "is_split": False, "column_mapping": {}}

    async def generate_quick_insight(self, filename: str, sample_data: str) -> str:
        """Analyze statistical profile and provide 3-5 concise insights."""
        prompt = f"""Task: Analyze the statistical profile of "{filename}" and provide 3-5 high-impact, extremely concise clinical insights.
Dataset:
{sample_data}
Insights:"""
        try:
            return await self._generate(prompt, "Quick Insight", temperature=0.5)
        except Exception:
            return "> [!IMPORTANT]\n> Baseline patterns inferred due to engine timeout."

    async def generate_followup_questions(self, filename: str, summary: str, sample_data: str) -> list[str]:
        """Generate insightful follow-up questions."""
        prompt = f"""Task: Based on Summary and Profile for "{filename}", generate 3 extremely concise, professional follow-up questions.
Summary: {summary}
Follow-up Questions (bullet points only):"""
        try:
            content = await self._generate(prompt, "Follow-up Questions", temperature=0.6)
            return [q.strip("- ").strip() for q in content.split('\n') if q.strip().startswith("-")][:4]
        except Exception:
            return ["What are the primary drivers behind the observed trends?"]

    async def generate_description(self, filename: str, sample_data: str, context: str = None) -> str:
        """Generate a clinical description for a data asset."""
        prompt = f"""Task: Provide a clinical, precise description for the dataset "{filename}".
Dataset Sample:
{sample_data[:5000]}
Context: {context or "No additional context."}
Description (max 2 sentences):"""
        try:
            return await self._generate(prompt, "Generate Description", temperature=0.3)
        except Exception:
            return f"Clinical data asset: {filename}"

    async def generate_assumptions(self, filename: str, sample_data: str) -> str:
        """Generate potential assumptions made during data analysis."""
        prompt = f"""Task: Analyze the statistical profile of "{filename}" and provide 2 extremely concise clinical assumptions.
Dataset Profile:
{sample_data[:5000]}
Assumptions (bullet points only):"""
        try:
            return await self._generate(prompt, "Assumptions", temperature=0.4)
        except Exception:
            return "- Data is representative of the period/context specified."

    async def generate_limitations(self, filename: str, sample_data: str) -> str:
        """Generate potential limitations and issues for the data."""
        prompt = f"""Task: Analyze the statistical profile of "{filename}" and identify 1-2 critical clinical limitations.
Dataset Profile:
{sample_data[:5000]}
Limitations (bullet points only):"""
        try:
            return await self._generate(prompt, "Limitations", temperature=0.4)
        except Exception:
            return "- Limited context on data collection methodology."

    async def generate_suggested_prompts(self, filename: str, summary: str, context: str) -> list[str]:
        """Generate high-impact analytical prompts based on summary and context."""
        prompt = f"""Task: Based on Summary and Conversation History for dataset "{filename}", generate 3 high-impact analytical prompts.
Summary: {summary}
Conversation History: {context}
Prompts (bullet points only):"""
        try:
            content = await self._generate(prompt, "Suggested Prompts", temperature=0.7)
            return [p.strip("- ").strip() for p in content.split('\n') if p.strip().startswith("-")][:3]
        except Exception:
            return ["Analyze the primary volume drivers."]

    async def generate_answer(self, filename: str, summary: str, context: str, question: str) -> str:
        """Generate a clinical, precise answer to a user question."""
        prompt = f"Context: Analyzing dataset \"{filename}\".\nSummary: {summary}\nConversation: {context}\nQuestion: {question}\nAnswer (max 3 sentences):"
        try:
            return await self._generate(prompt, "Agent Answer", temperature=0.4)
        except Exception as e:
            return f"> [!WARNING]\n> **Neural Link Interrupted**: {str(e)}"

    async def extract_insights(self, result_markdown: str) -> dict:
        """Parse a quick-insight markdown result into structured sections."""
        sections: dict[str, str] = {}
        current: str | None = None
        buf: list[str] = []
        for line in result_markdown.splitlines():
            heading = re.match(r"^##\s+(.+)", line)
            if heading:
                if current is not None: sections[current] = "\n".join(buf).strip()
                current = heading.group(1).strip()
                buf = []
            else: buf.append(line)
        if current is not None: sections[current] = "\n".join(buf).strip()

        def get_section(*names: str) -> str:
            for n in names:
                for k, v in sections.items():
                    if n.lower() in k.lower(): return v
            return ""

        key_insights_raw = get_section("Key Insights")
        bullets = [line.lstrip("-*• ").strip() for line in key_insights_raw.splitlines() if re.match(r"^\s*[-*•]\s+.{10,}", line)]
        
        if not bullets:
            prompt = f"Extract 3-7 standalone insights from:\n{key_insights_raw or result_markdown[:4000]}\nInsights (bullet points only):"
            try:
                raw = await self._generate(prompt, "Extract Insights", temperature=0.3)
                bullets = [line.lstrip("-*• ").strip() for line in raw.splitlines() if re.match(r"^\s*[-*•]\s+.{10,}", line)]
            except Exception: pass

        return {
            "bullets": bullets[:20],
            "assumptions": get_section("Assumptions"),
            "limitations": get_section("Known Limitation", "Limitations"),
            "metadata": {"basic_stats": get_section("Basic Stats"), "appendix": get_section("Appendix")},
        }

    async def generate_insights_summary(self, insights: list[str], days: int) -> str:
        """Generate an executive AI summary synthesizing all verified insights."""
        if not insights: return "> [!NOTE]\n> No verified insights available."
        bullet_block = "\n".join(f"- {i}" for i in insights)
        prompt = f"Synthesize these verified insights from the last {days} day(s) into an executive brief (bullet points only):\n{bullet_block}"
        try:
            return await self._generate(prompt, "Insights Summary", temperature=0.5)
        except Exception:
            return "\n".join(f"- {i}" for i in insights[:10])

    async def stream_answer(self, filename: str, summary: str, context: str, question: str) -> AsyncGenerator[str, None]:
        """Stream a clinical, precise answer to a user question."""
        prompt = f"{self.persona}\n\nContext: Analyzing dataset \"{filename}\".\nSummary: {summary}\nConversation: {context}\nQuestion: {question}\nAnswer:"
        async for token in self._ollama_client.stream(prompt):
            yield token

    # --- Data Intelligence ---

    async def generate_sql(self, question: str, table_name: str, schema_name: str = "main") -> Optional[str]:
        target_model = self.model_sql if self._ollama_client.mode != "cloud" else self._ollama_client.model
        return await tool_generate_sql(question, table_name, self._generate, target_model, schema_name)

    async def create_viz_payload(self, sql: str, original_question: str) -> Dict[str, Any]:
        return await tool_create_viz_payload(sql, original_question, self._generate, self.model_persona)

    async def process_question(self, question: str, table_name: str, schema_name: str = "main") -> AsyncGenerator[Any, None]:
        parser = JsonOutputParser(pydantic_object=AnalysisDecision)
        prompt = PromptTemplate.from_template("Does this require a chart?\nQuestion: \"{question}\"\n{format_instructions}")
        try:
            result = await self._generate(prompt.format(question=question, format_instructions=parser.get_format_instructions()), "Decision", parser=parser)
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
        return await self._ollama_client.check_connection()

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
    import argparse
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
    import asyncio
    asyncio.run(main())
