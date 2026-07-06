import requests

VISION_AGENT_URL = "http://localhost:5001"
SUPPLIER_AGENT_URL = "http://localhost:5002"

def discover_agent(base_url):
    """Fetch an agent's card to learn what it can do."""
    resp = requests.get(f"{base_url}/.well-known/agent.json")
    return resp.json()

def call_agent_skill(base_url, payload):
    resp = requests.post(f"{base_url}/invoke", json=payload)
    return resp.json()

def run_pipeline(image_path="flowers.png"):
    print("=== STEP 1: Discovering agents ===")
    vision_card = discover_agent(VISION_AGENT_URL)
    supplier_card = discover_agent(SUPPLIER_AGENT_URL)
    print(f"Found: {vision_card['name']} - {vision_card['description']}")
    print(f"Found: {supplier_card['name']} - {supplier_card['description']}\n")

    print("=== STEP 2: Vision Agent analyzes the image ===")
    vision_result = call_agent_skill(VISION_AGENT_URL, {"image_path": image_path})
    if "error" in vision_result:
        print(f"Vision Agent error: {vision_result['error']}")
        return
    description = vision_result["result"]
    print(f"Vision Agent says: {description}\n")

    print("=== STEP 3: Supplier Agent finds matching suppliers ===")
    supplier_result = call_agent_skill(SUPPLIER_AGENT_URL, {"description": description})
    matches = supplier_result["matches"]

    print("Top supplier matches:")
    for i, m in enumerate(matches, 1):
        print(f"{i}. {m['name']} — {m['item']} (distance: {m['distance']:.4f})")
        print(f"   {m['description']}")

    print("\n=== Pipeline complete ===")

if __name__ == "__main__":
    run_pipeline()