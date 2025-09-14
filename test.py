import PyQt5
import os
print("PyQt5 location:", PyQt5.__file__)

# 尝试查找plugins目录
pyqt5_path = os.path.dirname(PyQt5.__file__)
plugins_path = os.path.join(pyqt5_path, "Qt5", "plugins")
print("Plugins path:", plugins_path)
print("Path exists:", os.path.exists(plugins_path))

if os.path.exists(plugins_path):
    platforms_path = os.path.join(plugins_path, "platforms")
    print("Platforms path exists:", os.path.exists(platforms_path))
    if os.path.exists(platforms_path):
        print("Files in platforms directory:", os.listdir(platforms_path))

# 设置Qt插件路径
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r'h:\Projects\Bilibili直播表情包发送机\venv\Lib\site-packages\PyQt5\Qt5\plugins'