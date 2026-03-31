import pytest

from backend.app.services.rule_engine import check_ocr_result, validate_observation


def test_validate_observation_unit_conflict():
    is_valid, error = validate_observation("glucose", 5.6, "mg/dL")
    assert is_valid is False
    assert "单位不匹配" in error


def test_validate_observation_range_conflict():
    is_valid, error = validate_observation("axial_length", 55.0, "mm")
    assert is_valid is False
    assert "数值越界" in error


def test_check_ocr_result_missing_exam_date_and_side():
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
