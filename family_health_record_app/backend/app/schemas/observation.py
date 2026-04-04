from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import date
from typing import Optional, List


class ObservationBase(BaseModel):
    metric_code: str
    value_numeric: float
    unit: str
    side: Optional[str] = None

    @field_validator("value_numeric")
    @classmethod
    def validate_sanity_range(cls, v: float, info) -> float:
        metric = info.data.get("metric_code")
        if metric == "axial_length":
            if not (15.0 <= v <= 35.0):
                raise ValueError(f"眼轴数值 {v} 超出常规合理范围 (15-35mm)")
        elif metric == "height":
            if not (30.0 <= v <= 250.0):
                raise ValueError(f"身高数值 {v} 超出常规合理范围 (30-250cm)")
        elif metric == "weight":
            if not (2.0 <= v <= 500.0):
                raise ValueError(f"体重数值 {v} 超出常规合理范围 (2-500kg)")
        elif metric == "glucose":
            if not (0.1 <= v <= 50.0):
                raise ValueError(f"血糖数值 {v} 超出常规合理范围 (0.1-50.0 mmol/L)")
        elif metric == "ldl":
            if not (0.1 <= v <= 10.0):
                raise ValueError(f"低密度脂蛋白 {v} 超出常规合理范围 (0.1-10.0 mmol/L)")
        elif metric == "hemoglobin":
            if not (30.0 <= v <= 250.0):
                raise ValueError(f"血红蛋白 {v} 超出常规合理范围 (30-250 g/L)")
        elif metric == "hba1c":
            if not (3.0 <= v <= 15.0):
                raise ValueError(f"糖化血红蛋白 {v} 超出常规合理范围 (3.0-15.0%)")
        return v

class ManualExamCreate(BaseModel):
    exam_date: date
    institution_name: Optional[str] = None
    observations: List[ObservationBase]

    @field_validator("exam_date")
    @classmethod
    def validate_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("检查日期不能晚于当前系统时间")
        return v

class ObservationUpdate(BaseModel):
    value_numeric: float

    @field_validator("value_numeric")
    @classmethod
    def validate_update_range(cls, v: float) -> float:
        if not (0.0 < v <= 1000.0):
            raise ValueError("数值越界，必须大于 0 且不超过 1000")
        return v
