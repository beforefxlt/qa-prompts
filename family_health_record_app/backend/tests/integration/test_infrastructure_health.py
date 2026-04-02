"""
基础设施健康检查测试
验证 MinIO、数据库等基础设施正常工作
"""
import pytest
import os
from app.services.storage_client import storage_client, storage_settings


@pytest.mark.asyncio
async def test_minio_bucket_exists():
    """验证 MinIO bucket 存在且可访问"""
    try:
        storage_client.s3.head_bucket(Bucket=storage_settings.MINIO_BUCKET)
    except Exception as e:
        pytest.fail(f"MinIO bucket '{storage_settings.MINIO_BUCKET}' 不可访问: {e}")


@pytest.mark.asyncio
async def test_minio_upload_and_download():
    """验证 MinIO 上传下载功能"""
    test_key = "test/health-check.txt"
    test_content = b"health check content"
    
    # 上传
    storage_client.upload_file(test_content, test_key, "text/plain")
    
    # 下载
    downloaded = storage_client.get_file(test_key)
    assert downloaded == test_content, "上传下载内容不一致"
    
    # 清理
    storage_client.s3.delete_object(Bucket=storage_settings.MINIO_BUCKET, Key=test_key)


@pytest.mark.asyncio  
async def test_minio_directory_structure():
    """验证 MinIO 目录结构完整"""
    required_dirs = [
        "original/",
        "desensitized/",
    ]
    
    for dir_path in required_dirs:
        test_key = f"{dir_path}.health-check"
        try:
            storage_client.upload_file(b"check", test_key, "text/plain")
            storage_client.s3.delete_object(Bucket=storage_settings.MINIO_BUCKET, Key=test_key)
        except Exception as e:
            pytest.fail(f"目录 '{dir_path}' 不可写: {e}")
