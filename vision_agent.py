import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

with open("flowers.png", "rb") as f:
    image_bytes = f.read()

max_attempts = 5
wait_seconds = 20

for attempt in range(1, max_attempts + 1):
    print(f"Attempt {attempt} of {max_attempts}...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                "Count exactly how many flowers are in this image, broken down by color. "
                "Do not guess. Write and run Python code using image analysis to verify "
                "your count before answering. Show your reasoning."
            ],
            config=types.GenerateContentConfig(
                tools=[types.Tool(code_execution=types.ToolCodeExecution())]
            )
        )

        print("\nSuccess! Here's what Gemini did:\n")
        for part in response.candidates[0].content.parts:
            if part.text:
                print("TEXT:", part.text)
            if part.executable_code:
                print("\nCODE GEMINI WROTE:\n", part.executable_code.code)
            if part.code_execution_result:
                print("\nCODE OUTPUT:\n", part.code_execution_result.output)
        break  # stop the loop, we got a real answer

    except Exception as e:
        print(f"Failed on attempt {attempt}: {e}")
        if attempt < max_attempts:
            print(f"Waiting {wait_seconds} seconds before trying again...\n")
            time.sleep(wait_seconds)
        else:
            print("\nAll attempts failed. The service may be down longer than usual — try again later.")