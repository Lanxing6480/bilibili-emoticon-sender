"""
PyQt调试辅助文件 - 使用debugpy.debug_this_thread()
用于解决VSCode中PyQt断点无法中断的问题
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置调试环境变量
os.environ['QT_DEBUG_PLUGINS'] = '1'

# 导入debugpy并配置
try:
    import debugpy
    # 启用调试器
    debugpy.listen(5678)
    print("调试器已启动，端口: 5678")
    print("在VSCode中附加到进程进行调试...")

    # 等待调试器连接
    debugpy.wait_for_client()
    print("调试器已连接!")

    # 标记当前线程为可调试
    debugpy.debug_this_thread()
    print("当前线程已标记为可调试")

except ImportError:
    print("未安装debugpy，请运行: pip install debugpy")
    print("将使用标准模式运行...")

# 导入主应用
from main import main

if __name__ == '__main__':
    # 启动主应用
    main()