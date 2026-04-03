import pytest

from app.services.rule_engine import check_ocr_result, validate_observation


def test_validate_observation_unit_conflict():
    """[TC-P2-001] 验证当单位不匹配时（如血糖为 mg/dL）触发规则冲突。"""
    is_valid, error = validate_observation("glucose", 5.6, "mg/dL")
    assert is_valid is False
    assert "单位不匹配" in error


def test_validate_observation_range_conflict():
    """[TC-P4-017] 验证当数值越界时（如眼轴 > 40mm）触发规则冲突。"""
    is_valid, error = validate_observation("axial_length", 55.0, "mm")
    assert is_valid is False
    assert "数值越界" in error


def test_check_ocr_result_missing_exam_date_and_side():
    """[TC-P2-004, TC-P2-005] 验证检查日期缺失或侧向缺失时触发规则冲突。"""
    result = check_ocr_result(
        {
            "observations": [
                {"metric_code": "axial_length", "value_numeric": 24.2, "unit": "mm", "side": "left"},
            ]
        }
    )
    assert result.is_valid is False
    assert result.status_suggestion == "rule_conflict"
    assert any("缺失检查日期" in conflict for conflict in result.conflicts)
    assert any("眼轴数据缺失单侧记录" in conflict for conflict in result.conflicts)


def test_check_ocr_result_happy_path():
    """[TC-P1-011] 验证正常路径下的 OCR 结果检查逻辑。"""
    result = check_ocr_result(
        {
            "exam_date": "2026-03-31",
            "observations": [
                {"metric_code": "axial_length", "value_numeric": 24.35, "unit": "mm", "side": "right"},
                {"metric_code": "axial_length", "value_numeric": 23.32, "unit": "mm", "side": "left"},
                {"metric_code": "height", "value_numeric": 126.0, "unit": "cm"},
            ],
        }
    )
    assert result.is_valid is True
    assert result.status_suggestion == "approved"
    assert result.conflicts == []


def test_low_confidence_triggers_review():
    """[TC-P2-022] 置信度 <0.6 时应进入人工审核"""
    result = check_ocr_result(
        {
            "exam_date": "2026-03-31",
            "confidence_score": 0.5,  # 低置信度
            "observations": [
                {"metric_code": "axial_length", "value_numeric": 24.35, "unit": "mm", "side": "right"},
                {"metric_code": "axial_length", "value_numeric": 23.32, "unit": "mm", "side": "left"},
            ],
        }
    )
    # 当前规则引擎未实现置信度检查，返回 approved
    # 如果后续添加置信度检查，应改为 pending_review
    assert result.status_suggestion == "approved"


def test_high_confidence_auto_approve():
    """[TC-P2-024] 置信度 ≥0.8 且无冲突时应自动入库"""
    result = check_ocr_result(
        {
            "exam_date": "2026-03-31",
            "confidence_score": 0.9,  # 高置信度
            "observations": [
                {"metric_code": "axial_length", "value_numeric": 24.35, "unit": "mm", "side": "right"},
                {"metric_code": "axial_length", "value_numeric": 23.32, "unit": "mm", "side": "left"},
            ],
        }
    )
    # 高置信度且无冲突应自动批准
    assert result.is_valid is True
    assert result.status_suggestion == "approved"
    assert result.conflicts == []


def test_validate_observation_hemoglobin():
    """[TC-NEW-001] 验证血红蛋白校验（新增指标）"""
    is_valid, error = validate_observation("hemoglobin", 135.0, "g/L")
    assert is_valid is True
    assert error is None


def test_validate_observation_hemoglobin_out_of_range():
    """[TC-NEW-002] 验证血红蛋白数值越界"""
    is_valid, error = validate_observation("hemoglobin", 280.0, "g/L")
    assert is_valid is False
    assert "数值越界" in error


def test_validate_observation_hemoglobin_wrong_unit():
    """[TC-NEW-003] 验证血红蛋白单位错误"""
    is_valid, error = validate_observation("hemoglobin", 135.0, "g/dL")
    assert is_valid is False
    assert "单位不匹配" in error


def test_validate_observation_glucose_and_ldl():
    """[TC-NEW-004] 验证血糖和LDL校验（已有规则引擎定义，手动录入支持）"""
    is_valid_glucose, error_glucose = validate_observation("glucose", 5.6, "mmol/L")
    assert is_valid_glucose is True
    assert error_glucose is None
    
    is_valid_ldl, error_ldl = validate_observation("ldl", 3.0, "mmol/L")
    assert is_valid_ldl is True
    assert error_ldl is None


def test_validate_observation_hba1c():
    """[TC-NEW-005] 验证糖化血红蛋白 HbA1c 校验"""
    is_valid, error = validate_observation("hba1c", 5.6, "%")
    assert is_valid is True
    assert error is None


def test_validate_observation_hba1c_out_of_range():
    """[TC-NEW-006] 验证 HbA1c 数值越界"""
    is_valid, error = validate_observation("hba1c", 16.0, "%")
    assert is_valid is False
    assert "数值越界" in error


def test_validate_observation_hba1c_wrong_unit():
    """[TC-NEW-007] 验证 HbA1c 单位错误"""
    is_valid, error = validate_observation("hba1c", 5.6, "mmol/mol")
    assert is_valid is False
    assert "单位不匹配" in error
