from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv
from google import genai
import time

load_dotenv()
app = Flask(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- Agent Card: describes what this agent can do ---
AGENT_CARD = {
    "name": "VisionAgent",
    "description": "Analyzes images and counts/identifies objects using code execution, not guessing.",
    "url": "http://localhost:5001",
    "skills": [
        {
            "id": "analyze_image",
            "description": "Given an image path, returns a description of what it sees (counts, colors, categories).",
            "endpoint": "/invoke"
        }
    ]
}

@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card():
    return jsonify(AGENT_CARD)

@app.route("/invoke", methods=["POST"])
def invoke():
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

            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    {"mime_type": "image/png", "data": image_bytes},
                    prompt
                ],
                config={"tools": [{"code_execution": {}}]}
            )

            # Extract just the final text summary
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

if __name__ == "__main__":
    app.run(port=5001)