import subprocess
import os
from pathlib import Path
from jimwurst.core.config import settings

def run_dbt_command(command: str = "build") -> str:
    """
    Runs a dbt command in the transformation directory.
    Default command is 'build'.
    """
    # Note: Path will need to be updated after Phase 4 reorganization
    dbt_dir = Path(__file__).parent.parent.parent / "apps" / "transformation" / "dbt"
    
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
