import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, Engine
from ravioli.backend.core.config import settings

def get_db_connection():
    """Get a raw psycopg2 database connection."""
    try:
        conn = psycopg2.connect(
            host=settings.db_host,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            port=settings.db_port
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def get_engine() -> Engine:
    """Get a SQLAlchemy engine."""
    return create_engine(settings.database_url)

def ensure_schema(schema_name: str):
    """Ensure the specified schema exists."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_name)))
        conn.commit()
    print(f"Schema '{schema_name}' checked/created.")
