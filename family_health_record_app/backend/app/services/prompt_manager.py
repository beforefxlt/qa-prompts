import json

class PromptManager:
    """
    动态组合 OCR 提示词。
    将公共的输出格式要求与具体的单据提取逻辑分离。
    """
    
    # 公共指令：确保大模型输出稳定的格式
    COMMON_INSTRUCTIONS = """
必须以严格的 JSON 格式输出，不要输出任何额外的解释性文字，不要使用 markdown 代码块包裹（即不要包含 ```json 等标记）。
如果某个字段无法在图上找到且没有明确规则推导，则该字段不要或者填 null。
"""

    # 配置各个任务专有的提示词模版
    PROMPT_REGISTRY = {
        "eye_axial_length": {
            "description": "眼科医学单据识别专家（主要识别检查日期和双眼眼轴长度）。",
            "logic_steps": [
                "1. 找到单据中的 'Examination' 关键字，提取其后的日期并转换为 YYYY-MM-DD 格式。",
                "   注意：必须忽略年份 < 2022 的日期（如出生日期 2018），仅认可 2022 年及以后的日期作为检查日期。",
                "2. 寻找 'Axial length' 或 'AL' 关键字，识别其后的数值。",
                "3. 根据表头 'Right' (OD) 和 'Left' (OS) 的位置，将 AL 数值准确归类 OD -> right, OS -> left。"
            ],
            "json_schema": {
                "exam_date": "YYYY-MM-DD",
                "final_answer": "为何选择此日期的逻辑说明",
                "observations": [
                    {"metric_code": "axial_length", "value_numeric": 24.35, "unit": "mm", "side": "right"},
                    {"metric_code": "axial_length", "value_numeric": 23.32, "unit": "mm", "side": "left"}
                ]
            }
        },
        "blood_routine": {
            "description": "血常规化验单识别专家。",
            "logic_steps": [
                "1. 找到检验日期或报告日期，格式化为 YYYY-MM-DD。",
                "2. 提取白细胞(WBC)、红细胞(RBC)、血红蛋白(HGB)等关键指标的数值和单位。"
            ],
            "json_schema": {
                "exam_date": "YYYY-MM-DD",
                "observations": [
                    {"metric_code": "wbc", "value_numeric": 5.5, "unit": "10^9/L"}
                ]
            }
        }
    }

    @classmethod
    def get_prompt(cls, document_type: str = "eye_axial_length") -> str:
        # Fallback to default if not found
        if document_type not in cls.PROMPT_REGISTRY:
            document_type = "eye_axial_length"
            
        config = cls.PROMPT_REGISTRY[document_type]
        
        prompt_parts = []
        prompt_parts.append(f"你是一个{config['description']}")
        prompt_parts.append("请按以下步骤思考并提取数据：")
        
        for step in config['logic_steps']:
            prompt_parts.append(step)
            
        prompt_parts.append(cls.COMMON_INSTRUCTIONS)
        
        prompt_parts.append("期望的输出 JSON 示例格式如下：")
        prompt_parts.append(json.dumps(config['json_schema'], ensure_ascii=False, indent=2))
        
        return "\n".join(prompt_parts)

prompt_manager = PromptManager()
