import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("POSTGRES_URL")

try:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname = current_database();"))
        conn.commit()
    print("Killed all other backend connections.")
except Exception as e:
    print(f"Error: {e}")
