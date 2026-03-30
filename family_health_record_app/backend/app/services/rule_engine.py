from typing import Dict, Any, Tuple, Optional, List
from pydantic import BaseModel

class MetricRule(BaseModel):
    min_val: float
    max_val: float
    standard_unit: str

# 核心指标生理边界字典 (基于人类常识与 PRD)
METRIC_REGISTRY: Dict[str, MetricRule] = {
    "height": MetricRule(min_val=30.0, max_val=250.0, standard_unit="cm"),
    "weight": MetricRule(min_val=1.0, max_val=500.0, standard_unit="kg"),
    "glucose": MetricRule(min_val=0.1, max_val=50.0, standard_unit="mmol/L"),
    "tc": MetricRule(min_val=0.1, max_val=30.0, standard_unit="mmol/L"),
    "tg": MetricRule(min_val=0.1, max_val=30.0, standard_unit="mmol/L"),
    "hdl": MetricRule(min_val=0.1, max_val=10.0, standard_unit="mmol/L"),
    "ldl": MetricRule(min_val=0.1, max_val=10.0, standard_unit="mmol/L"),
    "axial_length": MetricRule(min_val=15.0, max_val=40.0, standard_unit="mm"),
}

class ValidationResult(BaseModel):
    is_valid: bool
    conflicts: List[str] = []
    status_suggestion: str = "rule_checking"

def validate_observation(metric_code: str, value: float, unit: str) -> Tuple[bool, Optional[str]]:
    """
    针对单点观测指标执行物理校验。
    返回: (是否通过, 错误详情)
    """
    rule = METRIC_REGISTRY.get(metric_code)
    if not rule:
        return True, None # 未定义规则的指标暂时放行

    # 单位校验
    if unit.lower() != rule.standard_unit.lower():
        return False, f"单位不匹配: 期望 {rule.standard_unit}, 实际 {unit}"

    # 生理阈值校验
    if not (rule.min_val <= value <= rule.max_val):
        return False, f"数值越界: {value} 不在合理范围 [{rule.min_val}, {rule.max_val}]"

    return True, None

def check_ocr_result(processed_items: Dict[str, Any]) -> ValidationResult:
    """
    对 OCR 结构化后的全清单执行完整性与冲突校验。
    """
    conflicts = []
    
    # 1. 物理检查单中必须包含的关键日期
    if not processed_items.get("exam_date"):
        conflicts.append("缺失检查日期 (exam_date)")

    # 2. 逐项指标核验
    observations = processed_items.get("observations", [])
    if not observations:
        conflicts.append("未提取到任何有效观测指标")

    for obs in observations:
        m_code = obs.get("metric_code")
        val = obs.get("value_numeric")
        unit = obs.get("unit")
        
        if val is None or not m_code:
            conflicts.append(f"指标 {m_code} 数据不完整")
            continue

        is_valid, error = validate_observation(m_code, val, unit)
        if not is_valid:
            conflicts.append(f"{m_code}: {error}")

    # 3. 左右眼配对校验 (仅针对眼轴)
    axial_items = [o for o in observations if o.get("metric_code") == "axial_length"]
    if axial_items:
        sides = [o.get("side") for o in axial_items]
        if not ("left" in sides and "right" in sides):
            conflicts.append("眼轴数据缺失单侧记录 (需左右对称)")

    return ValidationResult(
        is_valid=len(conflicts) == 0,
        conflicts=conflicts,
        status_suggestion="approved" if len(conflicts) == 0 else "rule_conflict"
    )
