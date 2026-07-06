import os
from dotenv import load_dotenv
import psycopg2
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
db_url = os.getenv("DATABASE_URL")

client = genai.Client(api_key=api_key)

# Sample supplier data — feel free to edit these later
suppliers = [
    {"name": "BrightBloom Co.", "item": "Yellow Daisies", "description": "Supplier of bright yellow daisy-style flowers, bulk orders, fast shipping."},
    {"name": "Petal & Co.", "item": "Pink Flowers", "description": "Specializes in soft pink decorative flowers for events and retail."},
    {"name": "Sunrise Supplies", "item": "Orange Blossoms", "description": "Provides orange and coral-toned flowers, mid-size wholesale orders."},
    {"name": "Garden Fresh Traders", "item": "Mixed Flower Packs", "description": "General flower supplier offering mixed color assortment packs."},
]

def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

conn = psycopg2.connect(db_url)
cur = conn.cursor()

for s in suppliers:
    embedding = get_embedding(s["description"])
    cur.execute(
        "INSERT INTO suppliers (name, item, description, embedding) VALUES (%s, %s, %s, %s)",
        (s["name"], s["item"], s["description"], embedding)
    )
    print(f"Added supplier: {s['name']}")

conn.commit()
cur.close()
conn.close()

print("\nAll suppliers added with embeddings!")