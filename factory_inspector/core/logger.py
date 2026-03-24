import logging
import os

def setup_logger(log_file="inspection.log"):
    """配置全局日志记录器，用于记录原始监测数据"""
    logger = logging.getLogger("factory_inspector")
    logger.setLevel(logging.INFO)
    
    # 防止重复添加 handler
    if not logger.handlers:
        # 文件处理器
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

def get_logger():
    return logging.getLogger("factory_inspector")
