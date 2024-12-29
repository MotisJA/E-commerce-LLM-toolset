import logging
import os
from datetime import datetime

def setup_logging():
    # 创建logs目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                f'logs/app_{datetime.now().strftime("%Y%m%d")}.log'
            ),
            logging.StreamHandler()
        ]
    )
