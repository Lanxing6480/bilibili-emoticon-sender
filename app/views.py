# app/views.py
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QListWidgetItem, QGridLayout, QLineEdit, QPushButton,
                             QLabel, QSpinBox, QCheckBox, QScrollArea, QFrame, QMessageBox,
                             QSizePolicy,QSlider, QComboBox)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont
from typing import Dict, List

# 从同级目录的 config.py 中导入默认值
from . import config

import logging

class EmoticonButton(QPushButton):
    """
    自定义的表情按钮控件
    - 点击时，会发出一个包含自身表情数据的信号 `clicked_with_data`
    - 创建后，会发出一个请求加载图片的信号 `request_image_load`
    """
    # 定义自定义信号
    # 信号1: 当按钮被点击时，发射自己的表情数据
    clicked_with_data = pyqtSignal(dict)
    # 信号2: 当按钮被创建时，请求控制器加载并设置其图标
    request_image_load = pyqtSignal(object, str, str) # 参数: 按钮实例, 图片url, 表情id

    def __init__(self, emoticon_data: dict, initial_size: int, parent=None):
        super().__init__(parent)
        self.emoticon_data = emoticon_data
        
        # # 统一设置按钮外观
        # self.setFixedSize(128, 128)
        # self.setIconSize(QSize(112, 112))
        # 【修改】不再硬编码尺寸，而是根据传入的尺寸初始化
        self.update_size(initial_size)
        self.setToolTip(f"{self.emoticon_data['name']}\n类型: {self.emoticon_data['type']}")
        
        # 连接内置的 clicked 信号到一个自定义的槽函数
        self.clicked.connect(self._on_click)

    def _on_click(self):
        """内部槽函数，当按钮被点击时，发射带有数据的自定义信号。"""
        self.clicked_with_data.emit(self.emoticon_data)

    def set_icon_from_path(self, path: str):
        """
        由控制器调用的方法，用于在图片加载完成后设置按钮的图标。
        """
        if path and isinstance(path, str):
            pixmap = QPixmap(path)
            self.setIcon(QIcon(pixmap))
        else:
            # 如果图片加载失败，显示表情名字的前4个字符作为回退
            self.setText(self.emoticon_data["name"][:4])

    def update_size(self, icon_size: int):
        """根据给定的图标大小更新按钮和图标的尺寸"""
        button_size = icon_size + 16  # 按钮比图标稍大一些，留出边距
        self.setFixedSize(button_size, button_size)
        self.setIconSize(QSize(icon_size, icon_size))


class EmoticonPackageWidget(QWidget):
    """
    用于网格布局展示一个表情包内所有表情的容器控件。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout()
        # 设置布局，让按钮之间没有多余的间隙
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.emoticon_buttons = []

        self._current_emoticons = []
        self._current_cols = 0
        self._current_icon_size = config.ICON_SIZE # 默认图标大小

    def minimumSizeHint(self):
        """
        重写minimumSizeHint方法，欺骗QScrollArea。
        我们告诉它，我们的最小宽度是0，这样QScrollArea就会无条件地
        根据自己的可视区域宽度来调整我们的宽度。
        而高度则由布局正常计算。
        """
        # 返回一个宽度为0，高度由父类正常计算的尺寸
        return QSize(0, super().minimumSizeHint().height())

    def resizeEvent(self, event):
        """当窗口大小改变时，重新计算布局。"""
        super().resizeEvent(event)
        #logging.debug(f"当前容器宽度{self.width()}")
        self._relayout_emoticons()

    def set_emoticons(self, emoticons: list):
        """
        清空并使用新的表情数据填充网格。
        """
        logging.info(f"开始填充新表情包")
        # 步骤1: 清理旧的按钮
        for button in self.emoticon_buttons:
            self.layout.removeWidget(button)
            button.deleteLater() # 延迟删除，更安全
        self.emoticon_buttons.clear()
        
        # 步骤2: 添加新的按钮
        # row, col = 0, 0
        # max_cols = 5  # 每行最多显示5个表情

        self._current_emoticons = emoticons
        
        for emoticon in emoticons:
            button = EmoticonButton(emoticon, self._current_icon_size, self)
            self.emoticon_buttons.append(button)

        self._relayout_emoticons(True)

    def set_icon_size(self, size: int):
        """设置所有表情图标的大小并重新布局。"""
        self._current_icon_size = size
        for button in self.emoticon_buttons:
            button.update_size(size)
        #logging.debug(f"当前容器宽度{self.width()}，按钮大小{self._current_icon_size + 16 + self.layout.spacing()}")
        self._relayout_emoticons()

    def _relayout_emoticons(self,forced_relayout = False):
        """根据当前控件宽度和图标大小，计算列数并重新排列按钮。"""
        # logging.debug("已触发重排")
        if not self.emoticon_buttons:
            # logging.debug("重排因为没有表情按键而退出")
            return

        container_width = self.width()
        button_width = self._current_icon_size + 16 + self.layout.spacing()
        
        # 至少显示一列
        new_cols = max(1, container_width // button_width)
        
        # 如果列数没有变化，则无需重新布局，以提高性能
        if new_cols == self._current_cols and not forced_relayout:
            #logging.debug("重排因为列数没有变化而退出")
            return
            
        self._current_cols = new_cols
        
        # 重新将所有按钮添加到布局中
        row, col = 0, 0
        for button in self.emoticon_buttons:
            # addWidget 会自动移动已存在的 widget
            self.layout.addWidget(button, row, col)
            col += 1
            if col >= self._current_cols:
                col = 0
                row += 1

        logging.info(f"重排已完成，当然容器宽度{container_width}，按钮大小{button_width}，布局{new_cols}")


class MainWindow(QMainWindow):
    """
    主窗口视图。
    负责组装所有UI组件，但不处理任何业务逻辑。
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bilibili直播表情包发送机 (v2.1)")
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()

    def init_ui(self):
        """初始化整体UI布局。"""
        # 中央窗口和主垂直布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. 创建顶部的配置区域
        config_widget = self._create_config_widget()
        main_layout.addWidget(config_widget)
        
        # 分割线，美化界面
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # 2. 创建下部的内容区域
        content_widget = self._create_content_widget()
        main_layout.addWidget(content_widget)
        
        # 3. 添加状态栏
        self.statusBar().showMessage("准备就绪。请先填写配置并加载表情包。")
        
    def _create_config_widget(self) -> QWidget:
        """创建顶部的配置控件区域。"""
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        config_layout.setContentsMargins(0, 5, 0, 5)

        # 第一行配置：房间号、Cookie、加载按钮
        row1_layout = QHBoxLayout()
        row1_layout.addWidget(QLabel("直播间ID:"))
        self.room_id_combo = QComboBox()
        self.room_id_combo.setEditable(True)  # 允许用户手动输入
        self.room_id_combo.setPlaceholderText("选择或输入直播间ID")
        self.room_id_combo.setMinimumWidth(150)
        row1_layout.addWidget(self.room_id_combo)
        
        row1_layout.addWidget(QLabel("Cookie:"))
        self.cookie_edit = QLineEdit(config.DEFAULT_COOKIE)
        self.cookie_edit.setEchoMode(QLineEdit.Password) # Cookie内容以密码形式显示
        self.cookie_edit.setPlaceholderText("请在此处粘贴您的B站Cookie")
        row1_layout.addWidget(self.cookie_edit)
        
        self.load_emoticons_btn = QPushButton("🚀 加载表情包")
        self.load_emoticons_btn.setIconSize(QSize(16, 16))
        row1_layout.addWidget(self.load_emoticons_btn)
        
        config_layout.addLayout(row1_layout)
        
        # 第二行配置：发送选项、功能按钮
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(QLabel("发送间隔(秒):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)
        self.interval_spin.setValue(5)
        self.interval_spin.setToolTip("设置自动发送时每个表情之间的间隔时间")
        row2_layout.addWidget(self.interval_spin)
        
        self.loop_check = QCheckBox("循环发送")
        self.loop_check.setToolTip("勾选后，发送队列中的表情将会循环发送，而不是发送完毕后停止")
        row2_layout.addWidget(self.loop_check)

        # 添加一个新的按钮，用于快速发送
        self.quick_send_check = QCheckBox("快速发送")
        self.quick_send_check.setToolTip("勾选后，点击表情包列表中的表情会立即发送，而不是添加到队列")
        row2_layout.addWidget(self.quick_send_check)
        
        row2_layout.addStretch() # 添加弹性空间，让按钮靠右
        
        self.start_btn = QPushButton("▶️ 开始发送")
        self.start_btn.setToolTip("开始/停止自动发送队列中的表情")
        row2_layout.addWidget(self.start_btn)
        
        self.clear_queue_btn = QPushButton("🗑️ 清空队列")
        row2_layout.addWidget(self.clear_queue_btn)
        
        self.save_config_btn = QPushButton("💾 保存配置")
        row2_layout.addWidget(self.save_config_btn)
        
        config_layout.addLayout(row2_layout)
        return config_widget

    def _create_content_widget(self) -> QWidget:
        """创建中央的内容显示区域。"""
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)

        # 内容区左侧：表情包列表和发送队列
        left_frame = QFrame()
        left_frame.setFixedWidth(250)
        left_layout = QVBoxLayout(left_frame)
        
        left_layout.addWidget(QLabel("表情包列表"))
        self.package_list = QListWidget()
        left_layout.addWidget(self.package_list)
        
        left_layout.addWidget(QLabel("发送队列 (点击表情添加)"))
        self.send_queue_list = QListWidget()
        left_layout.addWidget(self.send_queue_list)

        # 内容区右侧：表情展示区
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)

        # 在右侧顶部添加尺寸控制条
        size_control_layout = QHBoxLayout()
        size_control_layout.addWidget(QLabel("图标大小:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(48, 128) # 设置图标大小范围
        self.size_slider.setValue(config.ICON_SIZE)      # 默认值
        self.size_slider.setTickPosition(QSlider.TicksBelow)
        self.size_slider.setTickInterval(16)
        size_control_layout.addWidget(self.size_slider)
        
        self.size_label = QLabel(f"{config.ICON_SIZE}px") # 用于显示当前尺寸
        self.size_label.setFixedWidth(50)
        size_control_layout.addWidget(self.size_label)
        right_layout.addLayout(size_control_layout)

        
        right_layout.addWidget(QLabel("表情预览"))
        self.emoticon_widget = EmoticonPackageWidget()
        
        # 为表情展示区添加滚动条
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.emoticon_widget)
        scroll_area.setWidgetResizable(True)
        # 强制关闭水平滚动条
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)
        right_layout.addWidget(scroll_area)
        
        content_layout.addWidget(left_frame)
        content_layout.addWidget(right_frame)

        # 连接滑块信号到处理函数
        self.size_slider.valueChanged.connect(self._on_icon_size_changed)
        return content_widget

    def show_message(self, title: str, message: str, level: str = "info"):
        """
        显示一个模式对话框（消息盒子），由控制器调用。
        level可以是 'info', 'warning', 'error'。
        """
        if level == "info":
            QMessageBox.information(self, title, message)
        elif level == "warning":
            QMessageBox.warning(self, title, message)
        elif level == "error":
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)
            
    def set_status(self, message: str, timeout: int = 4000):
        """在状态栏显示消息，由控制器调用。"""
        self.statusBar().showMessage(message, timeout)

    def toggle_sending_state(self, is_sending: bool):
        """根据发送状态切换按钮的文本和可用性。"""
        if is_sending:
            self.start_btn.setText("⏸️ 停止发送")
            self.clear_queue_btn.setEnabled(False)
            self.load_emoticons_btn.setEnabled(False)
        else:
            self.start_btn.setText("▶️ 开始发送")
            self.clear_queue_btn.setEnabled(True)
            self.load_emoticons_btn.setEnabled(True)

    def populate_package_list(self, emoticons: dict):
        """清空并使用表情包数据填充左侧的列表。"""
        self.package_list.clear()
        if not emoticons:
            self.set_status("未能加载到任何表情包。")
            return
        
        for pkg_id, pkg_data in emoticons.items():
            # 在这里创建UI元素是正确的，因为这是视图层
            item = QListWidgetItem(pkg_data["name"])
            # Qt.UserRole 用于将非显示的元数据（这里是pkg_id）附加到列表项上
            item.setData(Qt.UserRole, pkg_id)
            self.package_list.addItem(item)

    def _on_icon_size_changed(self, value):
        """处理图标大小滑块变化的事件。"""
        self.size_label.setText(f"{value}px")
        self.emoticon_widget.set_icon_size(value)

    def update_room_combo(self, rooms: List[Dict[str, str]]):
        """
        更新直播间ID下拉选择框的内容。

        Args:
            rooms: 房间信息列表，每个元素包含 room_id 和 name
        """
        current_text = self.room_id_combo.currentText()
        self.room_id_combo.clear()

        # 添加缓存的房间
        for room in rooms:
            display_text = f"{room['name']} ({room['room_id']})"
            self.room_id_combo.addItem(display_text, room['room_id'])

        # 恢复之前的文本（如果存在）
        if current_text:
            self.room_id_combo.setCurrentText(current_text)

    def get_room_id(self) -> str:
        """
        获取当前选择的直播间ID。

        Returns:
            直播间ID字符串
        """
        current_data = self.room_id_combo.currentData()
        if current_data:
            return current_data
        # 如果用户手动输入，返回输入的文本
        return self.room_id_combo.currentText()