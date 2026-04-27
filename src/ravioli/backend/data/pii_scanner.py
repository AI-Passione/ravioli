import re
import pandas as pd
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class PIIScanner:
    """
    A lightweight, rule-based scanner for PII.
    """
    
    # Common PII patterns
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
        """
        Scans a single string for PII and returns the types found.
        """
        if not text or not isinstance(text, str):
            return []
            
        found = []
        for name, pattern in self.compiled_patterns.items():
            if pattern.search(text):
                found.append(name)
        return found

    def scan_dataframe(self, df: pd.DataFrame, sample_size: int = 100) -> bool:
        """
        Scans a sample of a DataFrame for PII.
        Returns True if any PII is detected.
        """
        if df.empty:
            return False
            
        logger.info(f"Starting PII scan on sample of {len(df)} rows")
        # Take a sample for performance
        sample = df.head(sample_size)
        
        for column in sample.columns:
            # Only scan object (string) columns
            if sample[column].dtype == 'object':
                logger.debug(f"Scanning column: {column}")
                for value in sample[column].dropna():
                    found = self.scan_string(str(value))
                    if found:
                        logger.info(f"PII detected in column '{column}': {found}")
                        return True
        logger.info("PII scan completed: No PII detected")
        return False

# Global instance
pii_scanner = PIIScanner()
