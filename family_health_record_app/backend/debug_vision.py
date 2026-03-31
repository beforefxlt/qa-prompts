import os
import base64
import httpx
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OCR_MODEL_NAME = os.getenv("OCR_MODEL_NAME")

async def debug_vision():
    test_image_path = os.path.join("..", "tests", "01.jpg")
    with open(test_image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"Model: {OCR_MODEL_NAME}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 尝试标准 OpenAI 格式
        payload = {
            "model": OCR_MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is in this image? Reply with JSON only."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        }
        
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Status: {response.status_code}")
        print(f"Full Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(debug_vision())
