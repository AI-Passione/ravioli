import subprocess
import os
from pathlib import Path
from ravioli.backend.core.config import settings

def run_dbt_command(command: str = "build") -> str:
    """
    Runs a dbt command in the transformation directory.
    Default command is 'build'.
    """
    dbt_dir = Path(__file__).parent.parent / "data" / "olap" / "transformation" / "dbt"
    
    try:
        result = subprocess.run(
            ["dbt", command],
            cwd=dbt_dir,
            capture_output=True,
            text=True,
            check=False
        )
        
        output = result.stdout
        if result.stderr:
            output += "\nErrors:\n" + result.stderr
            
        return output

    except Exception as e:
        return f"Error running dbt: {str(e)}"
