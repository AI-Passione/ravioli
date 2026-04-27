from ravioli.backend.core import models

def test_model_table_names():
    """Verify that all models have the correct table and schema names after the rename."""
    assert models.Analysis.__tablename__ == "analyses"
    assert models.Analysis.__table_args__["schema"] == "app"
    
    assert models.AnalysisLog.__tablename__ == "analysis_logs"
    assert models.AnalysisLog.__table_args__["schema"] == "app"
    
    assert models.DataSource.__tablename__ == "data_sources"
    assert models.DataSource.__table_args__["schema"] == "app"
    
    assert models.Insight.__tablename__ == "insights"
    assert models.Insight.__table_args__["schema"] == "app"

def test_model_relationships():
    """Verify relationships are correctly defined after renames."""
    # Analysis -> AnalysisLog
    assert "logs" in models.Analysis.__mapper__.relationships
    assert models.Analysis.__mapper__.relationships["logs"].mapper.class_ == models.AnalysisLog
    
    # AnalysisLog -> Analysis
    assert "analysis" in models.AnalysisLog.__mapper__.relationships
    assert models.AnalysisLog.__mapper__.relationships["analysis"].mapper.class_ == models.Analysis
    
    # Insight -> Analysis
    assert "analysis" in models.Insight.__mapper__.relationships
    assert models.Insight.__mapper__.relationships["analysis"].mapper.class_ == models.Analysis
