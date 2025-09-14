# app/logger_setup.py
import logging
import sys

def setup_logger():
    """配置应用程序的日志记录器"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
        handlers=[
            logging.FileHandler("app.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )