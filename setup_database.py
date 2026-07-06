import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv("DATABASE_URL")
print("DEBUG - value found:", db_url)
# Connect to the database
conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Enable the vector extension (lets Postgres store and search "embeddings")
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

cur.execute("DROP TABLE IF EXISTS suppliers;")
# Create a table to store suppliers
cur.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        item TEXT NOT NULL,
        description TEXT,
        embedding VECTOR(3072)
    );
""")

conn.commit()
cur.close()
conn.close()

print("Database setup complete! 'suppliers' table is ready.")