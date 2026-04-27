import sys
import os

# Add the src directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from sqlalchemy import text
from ravioli.backend.core.database import engine

def rename_tables():
    """
    Rename execution_logs to analysis_logs
    Rename uploaded_files to data_sources
    """
    statements = [
        "ALTER TABLE app.execution_logs RENAME TO analysis_logs;",
        "ALTER TABLE app.uploaded_files RENAME TO data_sources;"
    ]
    
    with engine.begin() as conn:
        for stmt in statements:
            try:
                print(f"Executing: {stmt}")
                conn.execute(text(stmt))
                print("Success.")
            except Exception as e:
                print(f"Error (probably already renamed): {e}")

if __name__ == "__main__":
    rename_tables()
