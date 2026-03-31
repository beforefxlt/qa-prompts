import os
import base64
import httpx
import asyncio
import json
import time
import sys

os.environ['PYTHONIOENCODING'] = 'utf-8'

# 用户提供的配置
SILICONFLOW_API_KEY = "sk-vxpzocjnvrneofatmmocgahhmhsmpanzrtlwfccxuwnscajd"
OCR_MODEL_NAME = "Qwen/Qwen2.5-VL-32B-Instruct"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

async def test_ocr():
    image_path = os.path.join("..", "tests", "01.jpg")
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    print(f"Reading image: {image_path}")
    with open(image_path, "rb") as f:
        img_data = f.read()
        print(f"Image size: {len(img_data) / 1024:.2f} KB")
        base64_image = base64.b64encode(img_data).decode('utf-8')

    payload = {
        "model": OCR_MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "提取图片中的医疗数据，以JSON格式返回。"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "stream": False
    }

    print(f"Sending request to {API_URL}...")
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            duration = time.time() - start_time
            print(f"Request took {duration:.2f} seconds")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("Success! Response content saved to response.json")
                with open("response.json", "w", encoding="utf-8") as f:
                    json.dump(response.json(), f, indent=2, ensure_ascii=False)
            else:
                print(f"Error Response: {response.text}")
                
    except httpx.TimeoutException:
        print("Error: Request timed out after 180 seconds.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_ocr())
