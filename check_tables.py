import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgres://postgres.hqofysaeqglnvdqljvkl:V9DiaDYTnqiTANta@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Checking tables in 'public' schema...")
        sql = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        result = conn.execute(sql)
        tables = [row[0] for row in result.fetchall()]
        print(f"Tables: {tables}")
except Exception as e:
    print(f"Database Error: {e}")
