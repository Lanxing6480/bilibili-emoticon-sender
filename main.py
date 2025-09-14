# main.py
import sys
from PyQt5.QtWidgets import QApplication
import qtmodern.styles
import qtmodern.windows
from PyQt5 import sip

from app.views import MainWindow
from app.models import EmoticonManager
from app.controllers import MainController
from app.logger_setup import setup_logger

import os

def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径。
    在开发环境中，路径是相对于脚本的；在打包后，路径是相对于临时目录的。
    """
    if getattr(sys, 'frozen', False):
        # 打包后，资源在临时目录中
        base_path = sys._MEIPASS
    else:
        # 开发模式下
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def main():
    """主运行函数"""

    # 确保 config.json 能被正确找到
    config_path = get_resource_path('config.json')
    setup_logger()
    
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    
    # Initialize MVC components
    view = MainWindow()
    model = EmoticonManager()
    controller = MainController(view=view, model=model)
    
    # Show the main window
    modern_window = qtmodern.windows.ModernWindow(view)
    modern_window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()