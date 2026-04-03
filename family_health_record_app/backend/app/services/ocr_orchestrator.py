import logging
import os
import base64
import json
import httpx
import re
import tempfile
from typing import Dict, Any
from uuid import UUID
from datetime import datetime
from dotenv import load_dotenv

from .rule_engine import check_ocr_result
from .image_processor import desensitize_image
from .prompt_manager import prompt_manager

load_dotenv()

logger = logging.getLogger(__name__)

SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
OCR_MODEL_NAME = os.getenv("OCR_MODEL_NAME", "Qwen/Qwen2.5-VL-32B-Instruct")

class OCROrchestrator:
    """
    OCR 处理编排器。负责从脱敏到多模态抽取、规则校验、入库流转。
    """
    
    async def _encode_image(self, file_path: str) -> str:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def process_document(self, document_id: UUID, file_url: str, document_type: str = "eye_axial_length") -> Dict[str, Any]:
        """
        开始全链路 OCR 流程。
        """
        logger.info(f"开始处理文档 {document_id}, 类型: {document_type}, 文件路径: {file_url}")
        
        # 从 MinIO 获取文件
        from .storage_client import storage_client, storage_settings
        try:
            # file_url 格式为 "bucket/key"，需要提取 key
            if file_url.startswith(f"{storage_settings.MINIO_BUCKET}/"):
                file_key = file_url[len(f"{storage_settings.MINIO_BUCKET}/"):]
            else:
                file_key = file_url
            original_bytes = storage_client.get_file(file_key)
        except Exception as e:
            logger.error(f"从 MinIO 获取文件失败: {file_url}, 错误: {e}")
            return {"status": "error", "message": "File not found"}

        try:
            # 1. 先执行脱敏处理（安全红线：绝不向公有云发送原图）
            desensitized_bytes = desensitize_image(original_bytes)

            # 将脱敏图写入临时文件用于 base64 编码
            with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
                tmp.write(desensitized_bytes)
                tmp_path = tmp.name

            try:
                base64_image = await self._encode_image(tmp_path)
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            prompt_content = prompt_manager.get_prompt(document_type)

            prompt_content = prompt_manager.get_prompt(document_type)

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.siliconflow.cn/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": OCR_MODEL_NAME,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt_content},
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
                
                if response.status_code != 200:
                    logger.error(f"SiliconFlow 响应异常: {response.status_code} - {response.text}")
                    raise Exception("AI 识别服务连接异常")

                result_json = response.json()
                llm_text = result_json['choices'][0]['message']['content']
                logger.debug(f"LLM 原始输出内容: {llm_text}")
                
                # 清理内容中的非法部分
                cleaned_text = llm_text.strip()
                
                # 移除 markdown 代码块
                if "```json" in cleaned_text:
                    cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
                elif "```" in cleaned_text:
                    # 尝试找到 JSON 对象
                    parts = cleaned_text.split("```")
                    for part in parts:
                        part = part.strip()
                        if part.startswith('{') or part.startswith('['):
                            cleaned_text = part
                            break
                
                # 确保是有效的 JSON（可能有前后的文字说明）
                # 查找第一个 { 或 [ 到最后一个 } 或 ] 的内容
                json_start = min(
                    cleaned_text.find('{') if '{' in cleaned_text else float('inf'),
                    cleaned_text.find('[') if '[' in cleaned_text else float('inf')
                )
                if json_start != float('inf'):
                    # 从找到的 { 或 [ 开始
                    json_str = cleaned_text[json_start:]
                    
                    # 尝试找到匹配的结束括号
                    if json_str.startswith('{'):
                        # 找到匹配的 }
                        depth = 0
                        for i, c in enumerate(json_str):
                            if c == '{':
                                depth += 1
                            elif c == '}':
                                depth -= 1
                            if depth == 0:
                                cleaned_text = json_str[:i+1]
                                break
                    elif json_str.startswith('['):
                        depth = 0
                        for i, c in enumerate(json_str):
                            if c == '[':
                                depth += 1
                            elif c == ']':
                                depth -= 1
                            if depth == 0:
                                cleaned_text = json_str[:i+1]
                                break
                
                try:
                    extracted_data = json.loads(cleaned_text)
                    logger.info(f"LLM 提取序列化成功: {extracted_data}")
                except json.JSONDecodeError as je:
                    logger.error(f"JSON 解析失败. 原始内容: {llm_text}, 清理后内容: {cleaned_text}")
                    raise Exception(f"AI 返回的数据格式无法解析: {str(je)}")

                # 2. 执行规则校验
                validation_result = check_ocr_result(extracted_data)
                
                # 3. 构造 OCR 抽取结果快照
                raw_extraction_record = {
                    "document_id": document_id,
                    "raw_json": extracted_data,
                    "processed_items": extracted_data,
                    "confidence_score": 0.95,
                    "rule_conflict_details": {"error": validation_result.conflicts} if not validation_result.is_valid else None
                }
                
                return {
                    "status": validation_result.status_suggestion,
                    "data": raw_extraction_record
                }

        except TimeoutError as e:
            logger.error(f"OCR 流程超时: {str(e)}")
            return {
                "status": "error",
                "message": f"AI Processing Timeout: {str(e)}"
            }
        except Exception as e:
            logger.exception(f"OCR 流程发生系统错误: {str(e)}")
            return {
                "status": "error",
                "message": f"AI Processing Failed: {str(e)}"
            }

ocr_orchestrator = OCROrchestrator()
