from flask import Flask, jsonify, request
import os
import psycopg2
from google import genai
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

AGENT_CARD = {
    "name": "SupplierAgent",
    "description": "Finds the best-matching supplier for a given item description using vector similarity search.",
    "url": "http://localhost:5002",
    "skills": [
        {
            "id": "find_supplier",
            "description": "Given a text description of an item, returns the top matching suppliers.",
            "endpoint": "/invoke"
        }
    ]
}

@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card():
    return jsonify(AGENT_CARD)

def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

@app.route("/invoke", methods=["POST"])
def invoke():
    data = request.get_json()
    query_description = data.get("description", "")

    query_embedding = get_embedding(query_description)
    embedding_str = str(query_embedding)

    cur.execute(
        """
        SELECT name, item, description, embedding <=> %s AS distance
        FROM suppliers
        ORDER BY distance ASC
        LIMIT 3;
        """,
        (embedding_str,)
    )
    results = cur.fetchall()

    matches = [
        {"name": r[0], "item": r[1], "description": r[2], "distance": float(r[3])}
        for r in results
    ]

    return jsonify({"matches": matches})

if __name__ == "__main__":
    app.run(port=5002)