import pytest
from unittest.mock import AsyncMock
from ravioli.ai.skills.communication import (
    generate_description,
    generate_followup_questions,
    generate_suggested_prompts,
    generate_answer,
    stream_answer
)

@pytest.mark.anyio
async def test_generate_description_success():
    mock_gen = AsyncMock(return_value="Clinical clinical.")
    res = await generate_description("test.csv", "data", mock_gen)
    assert res == "Clinical clinical."

@pytest.mark.anyio
async def test_generate_description_error():
    mock_gen = AsyncMock(side_effect=Exception("Failed"))
    res = await generate_description("test.csv", "data", mock_gen)
    assert res == "Clinical data asset: test.csv"

@pytest.mark.anyio
async def test_generate_followup_questions_success():
    mock_gen = AsyncMock(return_value="- Question 1?\n- Question 2?")
    res = await generate_followup_questions("test.csv", "sum", "data", mock_gen)
    assert res == ["Question 1?", "Question 2?"]

@pytest.mark.anyio
async def test_generate_followup_questions_error():
    mock_gen = AsyncMock(side_effect=Exception("Failed"))
    res = await generate_followup_questions("test.csv", "sum", "data", mock_gen)
    assert res == ["What are the primary drivers behind the observed trends?"]

@pytest.mark.anyio
async def test_generate_suggested_prompts_success():
    mock_gen = AsyncMock(return_value="- Prompt 1\n- Prompt 2")
    res = await generate_suggested_prompts("test.csv", "sum", "context", mock_gen)
    assert res == ["Prompt 1", "Prompt 2"]

@pytest.mark.anyio
async def test_generate_suggested_prompts_error():
    mock_gen = AsyncMock(side_effect=Exception("Failed"))
    res = await generate_suggested_prompts("test.csv", "sum", "context", mock_gen)
    assert res == ["Analyze the primary volume drivers."]

@pytest.mark.anyio
async def test_generate_answer_success():
    mock_gen = AsyncMock(return_value="Answer")
    res = await generate_answer("test.csv", "sum", "context", "Q?", mock_gen)
    assert res == "Answer"

@pytest.mark.anyio
async def test_generate_answer_error():
    mock_gen = AsyncMock(side_effect=Exception("Timeout"))
    res = await generate_answer("test.csv", "sum", "context", "Q?", mock_gen)
    assert "**Neural Link Interrupted**: Timeout" in res

@pytest.mark.anyio
async def test_stream_answer():
    async def mock_stream(prompt):
        yield "Hello"
        yield " World"
        
    res = []
    async for token in stream_answer("test.csv", "sum", "context", "Q?", "Persona", mock_stream):
        res.append(token)
    assert res == ["Hello", " World"]
