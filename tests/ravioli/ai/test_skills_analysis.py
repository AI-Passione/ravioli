import pytest
from unittest.mock import AsyncMock
from ravioli.ai.skills.analysis import (
    analyze_sheet_structure,
    generate_quick_insight,
    generate_assumptions,
    generate_limitations,
    extract_insights,
    generate_insights_summary
)

@pytest.mark.anyio
async def test_analyze_sheet_structure_success():
    mock_gen = AsyncMock(return_value='{"verdict": "ready", "header_row": 0}')
    res = await analyze_sheet_structure("Sheet1", "grid", mock_gen)
    assert res == {"verdict": "ready", "header_row": 0}

@pytest.mark.anyio
async def test_analyze_sheet_structure_parse_fail():
    mock_gen = AsyncMock(return_value='no json here')
    res = await analyze_sheet_structure("Sheet1", "grid", mock_gen)
    assert res["verdict"] == "reject"

@pytest.mark.anyio
async def test_analyze_sheet_structure_error():
    mock_gen = AsyncMock(side_effect=Exception("Failed"))
    res = await analyze_sheet_structure("Sheet1", "grid", mock_gen)
    assert res["verdict"] == "ready"

@pytest.mark.anyio
async def test_generate_quick_insight_success():
    mock_gen = AsyncMock(return_value="insight 1")
    res = await generate_quick_insight("test.csv", "data", mock_gen)
    assert res == "insight 1"

@pytest.mark.anyio
async def test_generate_quick_insight_error():
    mock_gen = AsyncMock(side_effect=Exception("Failed"))
    res = await generate_quick_insight("test.csv", "data", mock_gen)
    assert "Baseline patterns inferred" in res

@pytest.mark.anyio
async def test_generate_assumptions_success():
    mock_gen = AsyncMock(return_value="assumptions")
    res = await generate_assumptions("test.csv", "data", mock_gen)
    assert res == "assumptions"

@pytest.mark.anyio
async def test_generate_assumptions_error():
    mock_gen = AsyncMock(side_effect=Exception("Failed"))
    res = await generate_assumptions("test.csv", "data", mock_gen)
    assert "representative of the period" in res

@pytest.mark.anyio
async def test_generate_limitations_success():
    mock_gen = AsyncMock(return_value="limitations")
    res = await generate_limitations("test.csv", "data", mock_gen)
    assert res == "limitations"

@pytest.mark.anyio
async def test_generate_limitations_error():
    mock_gen = AsyncMock(side_effect=Exception("Failed"))
    res = await generate_limitations("test.csv", "data", mock_gen)
    assert "Limited context" in res

@pytest.mark.anyio
async def test_extract_insights():
    md = "## Key Insights\n- this is insight number 1\n- this is insight number 2\n## Assumptions\nAssumption 1"
    mock_gen = AsyncMock()
    res = await extract_insights(md, mock_gen)
    assert len(res["bullets"]) == 2
    assert res["bullets"][0] == "this is insight number 1"
    assert res["assumptions"] == "Assumption 1"

@pytest.mark.anyio
async def test_generate_insights_summary_success():
    mock_gen = AsyncMock(return_value="Summary of insights")
    res = await generate_insights_summary(["insight1"], 7, mock_gen)
    assert res == "Summary of insights"

@pytest.mark.anyio
async def test_generate_insights_summary_empty():
    mock_gen = AsyncMock()
    res = await generate_insights_summary([], 7, mock_gen)
    assert "No verified insights" in res

@pytest.mark.anyio
async def test_generate_insights_summary_error():
    mock_gen = AsyncMock(side_effect=Exception("Failed"))
    res = await generate_insights_summary(["insight1"], 7, mock_gen)
    assert "- insight1" in res
