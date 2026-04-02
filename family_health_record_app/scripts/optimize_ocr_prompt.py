import os
import base64
import httpx
import asyncio
import json
import time

# 配置
SILICONFLOW_API_KEY = "sk-vxpzocjnvrneofatmmocgahhmhsmpanzrtlwfccxuwnscajd"
OCR_MODEL_NAME = "Qwen/Qwen2.5-VL-32B-Instruct"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
# 使用绝对路径确保可靠
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_PATH = os.path.join(BASE_DIR, "tests", "01.jpg")

# 期待的结果映射
EXPECTED = {
    "exam_date": "2024-09-21",
    "al_right": 24.35,
    "al_left": 23.32
}

# Prompt 变体库
PROMPT_VARIANTS = [
    {
        "name": "Baseline",
        "prompt": """提取图片中的医疗数据，以JSON格式返回。包含 exam_date, observations (metric_code: axial_length)."""
    },
    {
        "name": "CoT_Expert",
        "prompt": """你是一个眼科医学单据识别专家。
请按以下步骤思考并提取数据：
1. 找到单据中的 'Examination' 关键字，提取其后的日期并转换为 YYYY-MM-DD 格式。注意：如果日期年份 < 2022（例如出生日期 2018），请忽略它，继续寻找真正的检查日期。
2. 寻找 'Axial length' 或 'AL' 关键字，识别其后的数值。
3. 根据表头 'Right' (OD) 和 'Left' (OS) 的位置，将 AL 数值准确归类。
只输出 JSON，格式如下：
{
  "exam_date": "YYYY-MM-DD",
  "observations": [
    {"metric_code": "axial_length", "value_numeric": 0.0, "side": "right"},
    {"metric_code": "axial_length", "value_numeric": 0.0, "side": "left"}
  ]
}"""
    },
    {
        "name": "FewShot_Constraint",
        "prompt": """识别眼科检查单数据。
关键约束：
- 检查日期通常在 'Examination' 字符串之后，如 '24-9-21' 应处理为 '2024-09-21'。
- 必须排除 2022 年之前的日期（如病人生日）。
- OD = 右眼 (right), OS = 左眼 (left)。

示例输入逻辑：
'Examination 1 of 24-9-21 ; Axial length AL 24.35mm 23.32'
输出：
{
  "exam_date": "2024-09-21",
  "observations": [
    {"metric_code": "axial_length", "value_numeric": 24.35, "side": "right"},
    {"metric_code": "axial_length", "value_numeric": 23.32, "side": "left"}
  ]
}

请对这张图片执行同样的提取，输出 JSON。"""
    }
]

async def run_test(variant):
    name = variant["name"]
    prompt = variant["prompt"]
    print(f"\n[Testing Variant: {name}]...")
    
    with open(IMAGE_PATH, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode('utf-8')

    payload = {
        "model": OCR_MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        start = time.time()
        response = await client.post(
            API_URL,
            headers={"Authorization": f"Bearer {SILICONFLOW_API_KEY}"},
            json=payload
        )
        duration = time.time() - start
        
        if response.status_code != 200:
            return {"name": name, "score": 0, "error": response.text}

        content = response.json()['choices'][0]['message']['content']
        print(f"Response (Time: {duration:.2f}s): {content[:200]}...")
        
        # 简单打分逻辑
        score = 0
        try:
            # 提取 JSON 部分
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            data = json.loads(json_str)
            
            if data.get("exam_date") == EXPECTED["exam_date"]:
                score += 40
            
            obs = data.get("observations", [])
            for item in obs:
                if item.get("side") == "right" and item.get("value_numeric") == EXPECTED["al_right"]:
                    score += 30
                if item.get("side") == "left" and item.get("value_numeric") == EXPECTED["al_left"]:
                    score += 30
        except:
            print(f"Failed to parse JSON for {name}")
            
        return {"name": name, "score": score, "result": content}

async def main():
    results = []
    for variant in PROMPT_VARIANTS:
        res = await run_test(variant)
        results.append(res)
    
    print("\n" + "="*30)
    print("FINAL SCORES:")
    for r in results:
        print(f"Variant: {r['name']:20} | Score: {r['score']}/100")
    print("="*30)

if __name__ == "__main__":
    asyncio.run(main())
