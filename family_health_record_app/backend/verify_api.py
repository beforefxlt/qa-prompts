import os
import base64
import httpx
import asyncio
import json

OPENROUTER_API_KEY = "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"
OCR_MODEL_NAME = "nvidia/nemotron-nano-12b-v2-vl:free"

PROMPT_TEMPLATE = """
你是一个专业的医疗检查单据识别专家。
请从这张图片中提取以下眼科检查指标，并以严格的 JSON 格式输出：
1. exam_date: 格式为 YYYY-MM-DD。
2. institution: 检查机构名称。
3. observations: 这是一个列表，每个项包含：
   - metric_code: 固定为 "axial_length" (眼轴长度)。
   - value_numeric: 数值（浮点数）。
   - unit: 单位（如 mm, D）。
   - side: "left" 或 "right"。

如果无法确定，请保持字段为空或 null。不要输出任何解释性文字，只输出符合格式的 JSON 对象。
"""

async def test_nemotron_vision():
    image_path = os.path.join("..", "tests", "01.jpg")
    print(f"Reading image from: {os.path.abspath(image_path)}")
    
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"Calling OpenRouter with model: {OCR_MODEL_NAME}...")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": OCR_MODEL_NAME,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT_TEMPLATE},
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
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print("\n--- AI Extracted Data ---\n")
            print(content)
        else:
            print("\n--- AI Error Result ---\n")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_nemotron_vision())
