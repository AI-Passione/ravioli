import psycopg2

db_url = "postgresql://ravioli_user:ravioli_password@localhost:5432/ravioli_db"

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    print("Adding has_pii column...")
    cur.execute("ALTER TABLE app.uploaded_files ADD COLUMN IF NOT EXISTS has_pii BOOLEAN DEFAULT FALSE;")
    
    conn.commit()
    print("Migration successful!")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Migration failed: {e}")
