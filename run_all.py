import threading
import time
import os
import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from google import genai
from google.genai import types
import psycopg2

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# =========================================================vision_invoke()
# VISION AGENT (its own Flask app, own port, own agent card)
# =========================================================
vision_app = Flask("vision_agent")

VISION_AGENT_CARD = {
    "name": "VisionAgent",
    "description": "Analyzes images and counts/identifies objects using code execution, not guessing.",
    "url": "http://localhost:5001",
    "skills": [{"id": "analyze_image", "description": "Given an image path, returns a description of what it sees.", "endpoint": "/invoke"}]
}

@vision_app.route("/.well-known/agent.json", methods=["GET"])
def vision_card():
    return jsonify(VISION_AGENT_CARD)

@vision_app.route("/invoke", methods=["POST"])
def vision_invoke():
    data = request.get_json()
    image_path = data.get("image_path", "flowers.png")
    prompt = (
        "Look at this image and count the flowers by color using code execution "
        "(write and run actual Python code to verify counts, don't guess). "
        "Then respond with ONE short plain sentence summarizing what you see, "
        "e.g. 'This image shows 7 orange, 8 yellow, and 7 pink flowers.'"
    )
    for attempt in range(5):
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=[image_part, prompt],
                config={"tools": [{"code_execution": {}}]}
            )
            summary = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    summary += part.text
            return jsonify({"result": summary.strip()})
        except Exception as e:
            if "503" in str(e) and attempt < 4:
                time.sleep(20)
                continue
            return jsonify({"error": str(e)}), 500

# =========================================================
# SUPPLIER AGENT (its own Flask app, own port, own agent card)
# =========================================================
supplier_app = Flask("supplier_agent")

SUPPLIER_AGENT_CARD = {
    "name": "SupplierAgent",
    "description": "Finds the best-matching supplier for a given item description using vector similarity search.",
    "url": "http://localhost:5002",
    "skills": [{"id": "find_supplier", "description": "Given a text description, returns top matching suppliers.", "endpoint": "/invoke"}]
}

@supplier_app.route("/.well-known/agent.json", methods=["GET"])
def supplier_card():
    return jsonify(SUPPLIER_AGENT_CARD)

def get_embedding(text):
    result = client.models.embed_content(model="gemini-embedding-001", contents=text)
    return result.embeddings[0].values

@supplier_app.route("/invoke", methods=["POST"])
def supplier_invoke():
    data = request.get_json()
    query_description = data.get("description", "")
    query_embedding = get_embedding(query_description)
    embedding_str = str(query_embedding)

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name, item, description, embedding <=> %s AS distance
        FROM suppliers ORDER BY distance ASC LIMIT 3;
        """,
        (embedding_str,)
    )
    results = cur.fetchall()
    cur.close()
    conn.close()

    matches = [{"name": r[0], "item": r[1], "description": r[2], "distance": float(r[3])} for r in results]
    return jsonify({"matches": matches})

# =========================================================
# RUN BOTH SERVERS IN BACKGROUND THREADS
# =========================================================
def run_vision():
    vision_app.run(port=5001, use_reloader=False)

def run_supplier():
    supplier_app.run(port=5002, use_reloader=False)

threading.Thread(target=run_vision, daemon=True).start()
threading.Thread(target=run_supplier, daemon=True).start()

print("Starting Vision Agent (port 5001) and Supplier Agent (port 5002)...")
time.sleep(3)  # give both servers a moment to boot up

# =========================================================
# ORCHESTRATOR: discover agents, then run the pipeline
# =========================================================
def discover_agent(base_url):
    return requests.get(f"{base_url}/.well-known/agent.json").json()

def call_agent_skill(base_url, payload):
    return requests.post(f"{base_url}/invoke", json=payload).json()

def run_pipeline(image_path="flowers.png"):
    print("\n=== STEP 1: Discovering agents ===")
    v_card = discover_agent("http://localhost:5001")
    s_card = discover_agent("http://localhost:5002")
    print(f"Found: {v_card['name']} - {v_card['description']}")
    print(f"Found: {s_card['name']} - {s_card['description']}")

    print("\n=== STEP 2: Vision Agent analyzes the image ===")
    vision_result = call_agent_skill("http://localhost:5001", {"image_path": image_path})
    if "error" in vision_result:
        print(f"Vision Agent error: {vision_result['error']}")
        return
    description = vision_result["result"]
    print(f"Vision Agent says: {description}")

    print("\n=== STEP 3: Supplier Agent finds matching suppliers ===")
    supplier_result = call_agent_skill("http://localhost:5002", {"description": description})
    matches = supplier_result["matches"]
    print("Top supplier matches:")
    for i, m in enumerate(matches, 1):
        print(f"{i}. {m['name']} — {m['item']} (distance: {m['distance']:.4f})")
        print(f"   {m['description']}")

    print("\n=== Pipeline complete ===")

run_pipeline()