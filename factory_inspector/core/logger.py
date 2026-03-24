import logging
import os

def setup_logger(log_file="inspection.log"):
    """配置全局日志记录器，用于记录原始监测数据"""
    logger = logging.getLogger("factory_inspector")
    logger.setLevel(logging.INFO)
    
    # 防止重复添加 handler
    if not logger.handlers:
        try:
            # 文件处理器
            file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, IOError) as e:
            # 如果无法创建日志文件，则退回到仅打印控制台模块 (通过 warnings 或直接忽略)
            print(f"⚠️ 无法创建日志文件 {log_file}: {e}. 审计日志将无法记录。")
            
    return logger

def get_logger():
    return logging.getLogger("factory_inspector")
