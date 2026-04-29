import os
import re
import logging
import pandas as pd
import dlt
from pathlib import Path
from typing import List, Dict, Any, Optional
from ravioli.backend.core.config import settings

logger = logging.getLogger(__name__)

# --- Pipeline Utils ---
def create_ravioli_pipeline(pipeline_name: str, dataset_name: str = "main"):
    """Creates a dlt pipeline configured to use the Ravioli DuckDB instance."""
    return dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=dlt.destinations.duckdb(str(settings.duckdb_path)),
        dataset_name=dataset_name
    )

# --- PII Scanning ---
class PIIScanner:
    """A lightweight, rule-based scanner for PII."""
    PATTERNS = {
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "phone": r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        "credit_card": r'\b(?:\d[ -]*?){13,16}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "ipv4": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    }

    def __init__(self):
        self.compiled_patterns = {name: re.compile(pattern) for name, pattern in self.PATTERNS.items()}

    def scan_string(self, text: str) -> List[str]:
        if not text or not isinstance(text, str): return []
        found = []
        for name, pattern in self.compiled_patterns.items():
            if pattern.search(text): found.append(name)
        return found

    def scan_dataframe(self, df: pd.DataFrame, sample_size: int = 100) -> bool:
        if df.empty: return False
        sample = df.head(sample_size)
        for column in sample.columns:
            if sample[column].dtype == 'object':
                for value in sample[column].dropna():
                    if self.scan_string(str(value)): return True
        return False

pii_scanner = PIIScanner()

# --- XLSX Processing Utils ---
def process_sheet_with_analysis(df: pd.DataFrame, analysis: dict) -> pd.DataFrame:
    """Apply structural fixes discovered by AI analysis."""
    h_idx = int(analysis.get("header_row", 0))
    d_idx = int(analysis.get("data_start_row", h_idx + 1))
    is_split = analysis.get("is_split", False)
    offsets = analysis.get("split_offsets", [])
    
    if not is_split:
        h = df.iloc[h_idx].tolist()
        seen = set()
        for i, val in enumerate(h):
            v = str(val).lower().strip()
            if v and "unnamed" not in v and v in seen:
                is_split = True
                offsets = [j for j, x in enumerate(h) if str(x).lower().strip() == str(h[0]).lower().strip() and j > 0]
                break
            seen.add(v)
            
    if is_split:
        data = reconcile_split_table(df, h_idx, d_idx, offsets)
    else:
        data = df.iloc[d_idx:].copy()
        data.columns = [str(x).strip() if pd.notna(x) else f"col_{i}" for i, x in enumerate(df.iloc[h_idx])]
        
    data = data.dropna(axis=1, how='all').dropna(axis=0, how='all')
    if analysis.get("column_mapping"):
        data = data.rename(columns={k: v for k, v in analysis["column_mapping"].items() if k in data.columns})
    return data

def reconcile_split_table(df: pd.DataFrame, h_idx: int, d_idx: int, offsets: list) -> pd.DataFrame:
    """Merge multiple side-by-side table blocks into a single vertical table."""
    offsets = sorted(list(set(offsets)))
    blocks = []
    blocks.append(extract_block(df, h_idx, d_idx, 0, offsets[0]))
    for i in range(len(offsets) - 1):
        blocks.append(extract_block(df, h_idx, d_idx, offsets[i], offsets[i+1]))
    blocks.append(extract_block(df, h_idx, d_idx, offsets[-1], df.shape[1]))
    return pd.concat([b for b in blocks if b is not None and not b.empty], ignore_index=True)

def extract_block(df: pd.DataFrame, h_idx: int, d_idx: int, s_col: int, e_col: int) -> pd.DataFrame:
    """Helper to extract and clean a single block from a split table."""
    h = [str(x).strip() if pd.notna(x) else f"col_{i}" for i, x in enumerate(df.iloc[h_idx, s_col:e_col])]
    b = df.iloc[d_idx:, s_col:e_col].copy()
    b.columns = h
    return b.dropna(axis=1, how='all').dropna(axis=0, how='all')
