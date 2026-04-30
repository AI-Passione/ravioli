import logging
from typing import List, Optional, AsyncGenerator

logger = logging.getLogger(__name__)

async def generate_description(filename: str, sample_data: str, generate_func, context: str = None) -> str:
    """Generate a clinical description for a data asset."""
    prompt = f"""Task: Provide a clinical, precise description for the dataset "{filename}".
Dataset Sample:
{sample_data[:5000]}
Context: {context or "No additional context."}
Description (max 2 sentences):"""
    try:
        return await generate_func(prompt, "Generate Description", temperature=0.3)
    except Exception:
        return f"Clinical data asset: {filename}"

async def generate_followup_questions(filename: str, summary: str, sample_data: str, generate_func) -> List[str]:
    """Generate insightful follow-up questions."""
    prompt = f"""Task: Based on Summary and Profile for "{filename}", generate 3 extremely concise, professional follow-up questions.
Summary: {summary}
Follow-up Questions (bullet points only):"""
    try:
        content = await generate_func(prompt, "Follow-up Questions", temperature=0.6)
        return [q.strip("- ").strip() for q in content.split('\n') if q.strip().startswith("-")][:4]
    except Exception:
        return ["What are the primary drivers behind the observed trends?"]

async def generate_suggested_prompts(filename: str, summary: str, context: str, generate_func) -> List[str]:
    """Generate high-impact analytical prompts based on summary and context."""
    prompt = f"""Task: Based on Summary and Conversation History for dataset "{filename}", generate 3 high-impact analytical prompts.
Summary: {summary}
Conversation History: {context}
Prompts (bullet points only):"""
    try:
        content = await generate_func(prompt, "Suggested Prompts", temperature=0.7)
        return [p.strip("- ").strip() for p in content.split('\n') if p.strip().startswith("-")][:3]
    except Exception:
        return ["Analyze the primary volume drivers."]

async def generate_answer(filename: str, summary: str, context: str, question: str, generate_func) -> str:
    """Generate a clinical, precise answer to a user question."""
    prompt = f"Context: Analyzing dataset \"{filename}\".\nSummary: {summary}\nConversation: {context}\nQuestion: {question}\nAnswer (max 3 sentences):"
    try:
        return await generate_func(prompt, "Agent Answer", temperature=0.4)
    except Exception as e:
        return f"> [!WARNING]\n> **Neural Link Interrupted**: {str(e)}"

async def stream_answer(filename: str, summary: str, context: str, question: str, persona: str, stream_func) -> AsyncGenerator[str, None]:
    """Stream a clinical, precise answer to a user question."""
    prompt = f"{persona}\n\nContext: Analyzing dataset \"{filename}\".\nSummary: {summary}\nConversation: {context}\nQuestion: {question}\nAnswer:"
    async for token in stream_func(prompt):
        yield token
