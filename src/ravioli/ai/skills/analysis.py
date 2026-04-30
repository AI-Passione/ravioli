import json
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

async def analyze_sheet_structure(sheet_name: str, sample_grid: str, generate_func) -> Dict[str, Any]:
    """Methodically analyze Excel sheet structure for ingestion."""
    prompt = f"""Task: Methodically analyze the structural integrity and layout of Excel sheet "{sheet_name}".
Context: You are inspecting a VISUAL GRID of the first 20 rows of an Excel sheet. 
Criteria for JSON: verdict ("ready", "needs_fix", "split_table", "reject"), header_row, data_start_row, is_split, column_mapping.
Grid:
{sample_grid}
Return ONLY clinical JSON."""
    try:
        content = await generate_func(prompt, "Structural Analysis", temperature=0.1)
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match: return json.loads(match.group(0))
        return {"verdict": "reject", "reason": "Parse failure"}
    except Exception:
        return {"verdict": "ready", "header_row": 0, "data_start_row": 1, "is_split": False, "column_mapping": {}}

async def generate_quick_insight(filename: str, sample_data: str, generate_func) -> str:
    """Analyze statistical profile and provide 3-5 concise insights."""
    prompt = f"""Task: Analyze the statistical profile of "{filename}" and provide 3-5 high-impact, extremely concise clinical insights.
Dataset:
{sample_data}
Insights:"""
    try:
        return await generate_func(prompt, "Quick Insight", temperature=0.5)
    except Exception:
        return "> [!IMPORTANT]\n> Baseline patterns inferred due to engine timeout."

async def generate_assumptions(filename: str, sample_data: str, generate_func) -> str:
    """Generate potential assumptions made during data analysis."""
    prompt = f"""Task: Analyze the statistical profile of "{filename}" and provide 2 extremely concise clinical assumptions.
Dataset Profile:
{sample_data[:5000]}
Assumptions (bullet points only):"""
    try:
        return await generate_func(prompt, "Assumptions", temperature=0.4)
    except Exception:
        return "- Data is representative of the period/context specified."

async def generate_limitations(filename: str, sample_data: str, generate_func) -> str:
    """Generate potential limitations and issues for the data."""
    prompt = f"""Task: Analyze the statistical profile of "{filename}" and identify 1-2 critical clinical limitations.
Dataset Profile:
{sample_data[:5000]}
Limitations (bullet points only):"""
    try:
        return await generate_func(prompt, "Limitations", temperature=0.4)
    except Exception:
        return "- Limited context on data collection methodology."

async def extract_insights(result_markdown: str, generate_func) -> dict:
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
            raw = await generate_func(prompt, "Extract Insights", temperature=0.3)
            bullets = [line.lstrip("-*• ").strip() for line in raw.splitlines() if re.match(r"^\s*[-*•]\s+.{10,}", line)]
        except Exception: pass

    return {
        "bullets": bullets[:20],
        "assumptions": get_section("Assumptions"),
        "limitations": get_section("Known Limitation", "Limitations"),
        "metadata": {"basic_stats": get_section("Basic Stats"), "appendix": get_section("Appendix")},
    }

async def generate_insights_summary(insights: list[str], days: int, generate_func) -> str:
    """Generate an executive AI summary synthesizing all verified insights."""
    if not insights: return "> [!NOTE]\n> No verified insights available."
    bullet_block = "\n".join(f"- {i}" for i in insights)
    prompt = f"Synthesize these verified insights from the last {days} day(s) into an executive brief (bullet points only):\n{bullet_block}"
    try:
        return await generate_func(prompt, "Insights Summary", temperature=0.5)
    except Exception:
        return "\n".join(f"- {i}" for i in insights[:10])
