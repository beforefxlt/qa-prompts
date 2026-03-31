import os
import base64
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# OCR_MODEL_NAME = "google/gemini-2.0-flash-exp:free"
OCR_MODEL_NAME = "qwen/qwen-turbo-vision:latest" # 尝试一个确定的 Vision 模型

async def diagnose():
    print(f"Testing API Key: {OPENROUTER_API_KEY[:10]}...")
    print(f"Testing Model: {OCR_MODEL_NAME}")
    
    # 模拟一个小图片或文字请求先验证 Key
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": OCR_MODEL_NAME,
                    "messages": [
                        {"role": "user", "content": "Hello, can you see this text?"}
                    ]
                }
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
