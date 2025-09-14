# app/controllers.py
import json
import logging
from PyQt5.QtCore import QTimer, QThread
from PyQt5.QtCore import Qt

# 控制器只从models和views导入它需要交互的类
from .models import EmoticonManager
from .views import MainWindow
from .threads import Worker

class MainController:
    """
    控制器 (Controller):
    - 监听来自视图(View)的信号 (如按钮点击)
    - 调用模型(Model)来处理数据 (如加载表情包)
    - 获取模型处理后的结果，并调用视图的方法来更新UI
    """
    def __init__(self, view: MainWindow, model: EmoticonManager):
        self.view = view
        self.model = model
        self.threadpool = []  # 用于保持对活动线程的引用，防止被垃圾回收
        self.send_queue = []
        self.is_sending = False
        
        self.sending_timer = QTimer()
        self.sending_timer.timeout.connect(self._send_next_from_queue)

        self._connect_signals()
        self.load_config()

    def _connect_signals(self):
        """将视图发出的信号连接到控制器的槽函数上。"""
        self.view.load_emoticons_btn.clicked.connect(self.load_emoticons)
        self.view.save_config_btn.clicked.connect(self.save_config)
        self.view.package_list.currentRowChanged.connect(self.display_package_emoticons)
        self.view.start_btn.clicked.connect(self.toggle_sending)
        self.view.clear_queue_btn.clicked.connect(self.clear_send_queue)
        self.view.quick_send_check.stateChanged.connect(self._on_quick_send_toggled)

    def _on_quick_send_toggled(self, state):
        """当快速发送开关切换时，切换开始按钮的可用性。"""
        is_checked = (state == Qt.Checked)
        is_enabled = not is_checked

        self.view.start_btn.setEnabled(is_enabled)
        self.view.clear_queue_btn.setEnabled(is_enabled)
        self.view.loop_check.setEnabled(is_enabled)
        self.view.send_queue_list.setEnabled(is_enabled)

        # 如果切换到快速发送模式时，自动发送正在运行，则停止它
        if is_checked and self.is_sending:
            self.toggle_sending()

    def _execute_in_thread(self, fn, on_success, on_error, *args, **kwargs):
        """通用函数，用于在后台线程中执行任何耗时操作。"""
        worker = Worker(fn, *args, **kwargs)
        thread = QThread()
        worker.moveToThread(thread)

        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        worker.signals.finished.connect(thread.quit)
        worker.signals.finished.connect(worker.deleteLater)
        
        thread.started.connect(worker.run)
        thread.start()
        self.threadpool.append((thread, worker)) # 保持引用
        return thread

    # --- 逻辑处理方法 ---

    def load_emoticons(self):
        """处理“加载表情包”按钮的点击事件。"""
        room_id_str = self.view.room_id_edit.text()
        cookie = self.view.cookie_edit.text()
        
        if not cookie or not room_id_str:
            self.view.show_message("错误", "请先填写直播间ID和Cookie。", "warning")
            return
            
        self.model.set_cookie(cookie)
        self.view.set_status("正在加载表情包，请稍候...")
        self.view.load_emoticons_btn.setEnabled(False)
        
        self._execute_in_thread(
            self.model.load_all_emoticons,
            on_success=self._on_emoticons_loaded,
            on_error=lambda err: self.view.show_message("加载失败", f"发生错误: {err[1]}", "error"),
            room_id=int(room_id_str)
        )

    def _on_emoticons_loaded(self, emoticons: dict):
        """当表情包数据从模型成功返回后的回调函数。"""
        self.view.populate_package_list(emoticons)
        
        self.view.set_status(f"成功加载了 {len(emoticons)} 个表情包。")
        self.view.load_emoticons_btn.setEnabled(True)
        logging.info("表情包数据已加载并传递给视图进行填充。")

    def display_package_emoticons(self, row: int):
        """处理左侧表情包列表的选择事件。"""
        if row < 0: return
        
        item = self.view.package_list.item(row)
        pkg_id = item.data(Qt.UserRole) # 从视图项获取数据
        pkg_data = self.model.emoticons.get(pkg_id)
        
        if pkg_data:
            emotes_with_type = [dict(e, type=pkg_data["type"]) for e in pkg_data["emotes"]]
            self.view.emoticon_widget.set_emoticons(emotes_with_type)
            
            # 为新创建的表情按钮连接信号
            for button in self.view.emoticon_widget.emoticon_buttons:
                button.clicked_with_data.connect(self.add_to_send_queue)
                button.request_image_load.connect(self._load_emoticon_image)
                # 立即触发图片加载请求
                button.request_image_load.emit(button, button.emoticon_data['url'], str(button.emoticon_data['id']))
                
    def _load_emoticon_image(self, button, url: str, emoticon_id: str):
        """在后台加载单个表情图片并更新对应的按钮。"""
        self._execute_in_thread(
            self.model.get_emoticon_image,
            on_success=button.set_icon_from_path,
            on_error=lambda err: logging.error(f"加载图片失败 {url}: {err[1]}"),
            url=url,
            emoticon_id=emoticon_id
        )

    # --- 发送逻辑 ---

    def add_to_send_queue(self, emoticon_data: dict):
        """将用户点击的表情添加到发送队列或立即发送。"""
        if self.view.quick_send_check.isChecked():
            # 新增一个独立的立即发送函数
            self.send_single_emoticon(emoticon_data)
            logging.info(f"快速发送: {emoticon_data['name']}")
        else:
            # Otherwise, add to the queue as usual
            self.send_queue.append(emoticon_data)
            self.view.send_queue_list.addItem(emoticon_data['name'])
            logging.info(f"已将 '{emoticon_data['name']}' 添加到发送队列。")

    def send_single_emoticon(self, emoticon_data: dict):
        """
        处理立即发送一个表情的逻辑。
        """
        room_id_str = self.view.room_id_edit.text()
        cookie = self.view.cookie_edit.text()

        if not cookie or not room_id_str:
            self.view.show_message("错误", "请先填写直播间ID和Cookie。", "warning")
            return
        
        self.view.set_status(f"正在快速发送: {emoticon_data['name']}...")
        room_id = int(room_id_str)
        
        self._execute_in_thread(
            self.model.send_emoticon,
            on_success=self._on_send_result,
            on_error=lambda err: self._on_send_result((False, str(err[1]))),
            room_id=room_id,
            emoticon_data=emoticon_data
        )


    def clear_send_queue(self):
        """清空发送队列。"""
        self.send_queue.clear()
        self.view.send_queue_list.clear()
        logging.info("发送队列已清空。")
        
    def toggle_sending(self):
        """切换自动发送的状态。"""
        self.is_sending = not self.is_sending
        self.view.toggle_sending_state(self.is_sending)

        if self.is_sending:
            if not self.send_queue:
                self.view.show_message("提示", "发送队列为空，请先点击表情添加到队列。", "warning")
                self.is_sending = False
                self.view.toggle_sending_state(False)
                return
            
            interval_ms = self.view.interval_spin.value() * 1000
            self.sending_timer.start(interval_ms)
            logging.info(f"开始自动发送，间隔 {interval_ms}ms。")
            self._send_next_from_queue() # 立即发送第一个
        else:
            self.sending_timer.stop()
            logging.info("已停止自动发送。")

    def _send_next_from_queue(self):
        """发送队列中的下一个表情。"""
        if not self.is_sending or not self.send_queue:
            if self.is_sending: self.toggle_sending() # 如果队列空了，自动停止
            return
            
        emoticon_data = self.send_queue[0]
        
        if self.view.loop_check.isChecked():
            # 循环模式：将队首元素移到队尾
            self.send_queue.append(self.send_queue.pop(0))
            item = self.view.send_queue_list.takeItem(0)
            self.view.send_queue_list.addItem(item)
        else:
            # 普通模式：移除队首元素
            self.send_queue.pop(0)
            self.view.send_queue_list.takeItem(0)
        
        self.view.set_status(f"正在发送: {emoticon_data['name']}...")
        room_id = int(self.view.room_id_edit.text())
        
        self._execute_in_thread(
            self.model.send_emoticon,
            on_success=self._on_send_result,
            on_error=lambda err: self._on_send_result((False, str(err[1]))),
            room_id=room_id,
            emoticon_data=emoticon_data
        )
        
    def _on_send_result(self, result: tuple):
        """处理表情发送后的结果。"""
        success, message = result
        status_text = "成功" if success else "失败"
        self.view.set_status(f"发送{status_text}: {message}")
        logging.info(f"发送结果: {success}, 消息: {message}")

    # --- 配置管理 ---

    def load_config(self):
        """加载配置文件。"""
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.view.room_id_edit.setText(str(config.get("room_id", "")))
                self.view.cookie_edit.setText(config.get("cookie", ""))
                self.view.interval_spin.setValue(config.get("interval", 5))
                self.view.loop_check.setChecked(config.get("loop", False))
                self.view.quick_send_check.setChecked(config.get("quick_send", False))
                self.view.size_slider.setValue(config.get("icon_size",84))
                logging.info("配置文件 config.json 加载成功。")
        except FileNotFoundError:
            logging.warning("未找到配置文件 config.json，将使用默认值。")
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")

    def save_config(self):
        """保存当前配置到文件。"""
        config_data = {
            "room_id": self.view.room_id_edit.text(),
            "cookie": self.view.cookie_edit.text(),
            "interval": self.view.interval_spin.value(),
            "loop": self.view.loop_check.isChecked(),
            "quick_send": self.view.quick_send_check.isChecked(),
            "icon_size": self.view.size_slider.value()
        }
        try:
            with open("config.json", "w") as f:
                json.dump(config_data, f, indent=4)
            self.view.show_message("成功", "配置已成功保存到 config.json。")
            logging.info("配置已保存。")
        except Exception as e:
            self.view.show_message("错误", f"保存配置失败: {e}", "error")