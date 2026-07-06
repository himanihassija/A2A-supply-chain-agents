import os
import psycopg2
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Connect to Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Connect to Postgres
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

def find_best_supplier(query_description, top_n=3):
    query_embedding = get_embedding(query_description)

    # pgvector needs the embedding as a string like '[0.1, 0.2, ...]'
    embedding_str = str(query_embedding)

    cur.execute(
        """
        SELECT name, item, description, embedding <=> %s AS distance
        FROM suppliers
        ORDER BY distance ASC
        LIMIT %s;
        """,
        (embedding_str, top_n)
    )
    results = cur.fetchall()
    return results

if __name__ == "__main__":
    # Test query - change this to whatever item you want to search for
    test_query = "fresh red roses for a wedding"
    print(f"Searching for suppliers matching: '{test_query}'\n")

    matches = find_best_supplier(test_query)

    for i, (name, item, description, distance) in enumerate(matches, 1):
        print(f"{i}. {name}")
        print(f"   Item: {item}")
        print(f"   Description: {description}")
        print(f"   Distance (lower = better match): {distance:.4f}")
        print()

    cur.close()
    conn.close()