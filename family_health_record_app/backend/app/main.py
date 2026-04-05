from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import engine
from .models.base import Base
from .routers.members import router as members_router
from .routers.documents import router as documents_router
from .routers.review import router as review_router
from .routers.trends import router as trends_router
from .routers.records import router as records_router
from .routers.admin import router as admin_router

app = FastAPI(title="家庭健康检查单管理 API", version="v1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(members_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(review_router, prefix="/api/v1")
app.include_router(trends_router, prefix="/api/v1")
app.include_router(records_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": "v1.3.0"}


@app.get("/api/v1/trends")
async def get_available_metrics():
    """返回系统支持的所有健康指标类型"""
    return {
        "metrics": [
            {"code": "axial_length", "name": "眼轴长度", "unit": "mm"},
            {"code": "vision_acuity", "name": "视力", "unit": ""},
            {"code": "height", "name": "身高", "unit": "cm"},
            {"code": "weight", "name": "体重", "unit": "kg"},
            {"code": "bmi", "name": "BMI指数", "unit": "kg/m²"},
            {"code": "heart_rate", "name": "心率", "unit": "bpm"},
            {"code": "blood_pressure_systolic", "name": "收缩压", "unit": "mmHg"},
            {"code": "blood_pressure_diastolic", "name": "舒张压", "unit": "mmHg"},
            {"code": "blood_glucose", "name": "血糖", "unit": "mmol/L"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
