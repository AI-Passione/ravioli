import json
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from ravioli.backend.data.olap.duckdb_manager import duckdb_manager

logger = logging.getLogger(__name__)

class VizStrategy(BaseModel):
    """Structured output for chart configuration."""
    chart_type: str = Field(description="The type of chart: 'bar', 'line', 'pie', or 'scatter'")
    labels_column: str = Field(description="The column name to use for the X-axis labels")
    values_columns: List[str] = Field(description="List of column names to use for the Y-axis values")
    title: str = Field(description="A clinical title for the chart")

async def create_viz_payload(
    sql: str, 
    original_question: str,
    generate_fn: Any,
    model: str
) -> Dict[str, Any]:
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
        
        config = await generate_fn(
            prompt_text=prompt.format(
                question=original_question,
                columns=df.columns.tolist(),
                sample_data=json.dumps(df.head(5).to_dict(orient='records')),
                format_instructions=parser.get_format_instructions()
            ),
            task_name="Viz Strategy",
            model=model,
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
