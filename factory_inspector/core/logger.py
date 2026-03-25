import logging
import os


def _remove_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass


def setup_logger(log_file="inspection.log"):
    """配置全局日志记录器，用于记录原始监测数据"""
    logger = logging.getLogger("factory_inspector")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    existing_target = None
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            existing_target = handler.baseFilename
            break

    # 同一日志文件则直接复用；切换目标文件时重绑 handler。
    if logger.handlers and existing_target == os.path.abspath(log_file):
        return logger

    _remove_handlers(logger)

    try:
        file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, IOError) as e:
        print(f"⚠️ 无法创建日志文件 {log_file}: {e}. 审计日志将无法记录。")

    return logger


def get_logger():
    return logging.getLogger("factory_inspector")
