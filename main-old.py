import sys
import json
import requests
import time
from datetime import datetime
from typing import List, Dict, Union
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QListWidget, QListWidgetItem, QGridLayout, QLineEdit, QPushButton,
                             QLabel, QComboBox, QSpinBox, QCheckBox, QScrollArea, QGroupBox,
                             QMessageBox, QTabWidget, QFrame, QSizePolicy, QToolBar)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QFont
import qtmodern.styles
import qtmodern.windows
import os

# ============== 配置区域 ==============
DEFAULT_COOKIE = "buvid3=1BACC6A1-FF10-D1A0-B07A-7C89C4E288C259655infoc; b_nut=1746519359; _uuid=2CA10D1EB-95D9-C810C-FC16-A9856471D10AC60223infoc; enable_web_push=DISABLE; enable_feed_channel=ENABLE; buvid4=FEA37573-D375-9094-4B10-F9F66D396AB360865-025050616-RnB5EqxY9tdVmWO9uTQIeA%3D%3D; rpdid=|(J|k)u~m~ku0J'u~RYlumJml; DedeUserID=432194698; DedeUserID__ckMd5=b13089bc2a02f5aa; hit-dyn-v2=1; buvid_fp_plain=undefined; LIVE_BUVID=AUTO7117465380984946; header_theme_version=OPEN; theme-tip-show=SHOWED; theme-avatar-tip-show=SHOWED; theme-switch-show=SHOWED; fingerprint=fdc2c04168810d5a9c0ed08e0334aa81; go-back-dyn=0; buvid_fp=9166f7dbfadd730e4f00bceb68cc0ecf; Hm_lvt_8a6e55dbd2870f0f5bc9194cddf32a02=1749989895,1750413472,1750486050,1750690948; SESSDATA=8d07865c%2C1768123448%2C86898%2A72CjAa48pG-ZF554N_0895j7UnjGR_UZt9drf0LbgRSrQWB4a_u5_Kz8VRLAqywLzmx_8SVmhsbjZ2OFdwc29MM2JuWDd0dUdEeDI4N09YVlMtRHh1bkk5akFKbnhoLVdSaU1SLVBXMUtpWVo0YkMybzk3SDhoUDN6WmZZTHlHUFRvb20yV0dUNWJRIIEC; bili_jct=c80c1e58f8fb55274dd7f56c048a9a4a; dy_spec_agreed=1; home_feed_column=5; browser_resolution=1912-954; CURRENT_QUALITY=120; sid=8ond0me3; bp_t_offset_432194698=1107216081845485568; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTY4OTE0MzUsImlhdCI6MTc1NjYzMjE3NSwicGx0IjotMX0.Sr0J8DDdAU2mQk9aeK5CW0bPYyrkSJjwI_oeW1SjnQY; bili_ticket_expires=1756891375; b_lsid=104CB887A_198FFF5BF82; bsource=search_bing; timeMachine=0; PVID=10; CURRENT_FNVAL=4048"
DEFAULT_ROOM_ID = 31586244

# API地址
GET_USER_EMOTICON_API = "https://api.bilibili.com/x/emote/user/panel/web"
GET_EMOTICON_PACKAGE_API = "https://api.bilibili.com/x/emote/package"
GET_LIVE_EMOTICON_API = "https://api.live.bilibili.com/xlive/web-ucenter/v2/emoticon/GetEmoticons"
SEND_DANMU_API = "https://api.live.bilibili.com/msg/send"
GET_CHARGE_EMOTICON_API = "https://api.bilibili.com/x/upowerv2/gw/rights/index"
GET_LIVE_INFORMATION = "https://api.live.bilibili.com/room/v1/Room/get_info"

# 设置Qt插件路径
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r'h:\Projects\Bilibili直播表情包发送机\venv\Lib\site-packages\PyQt5\Qt5\plugins'

class EmoticonManager:
    def __init__(self):
        self.emoticons = {}  # 存储所有表情包
        self.cookie = DEFAULT_COOKIE
        
    def set_cookie(self, cookie):
        self.cookie = cookie
        
    def get_csrf_from_cookie(self):
        """从Cookie中提取csrf_token"""
        try:
            cookie_dict = dict(pair.split('=', 1) for pair in self.cookie.split('; ') if '=' in pair)
            return cookie_dict.get('bili_jct', '')
        except:
            return ''
    
    def get_user_emoticons(self):
        """获取用户表情包列表"""
        headers = {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(GET_USER_EMOTICON_API, 
                                   params={"business": "reply"}, 
                                   headers=headers, 
                                   timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == 0:
                return data["data"]["packages"]
            else:
                print(f"获取用户表情包失败: {data['message']}")
                return []
        except Exception as e:
            print(f"获取用户表情包异常: {str(e)}")
            return []
    
    def get_emoticon_package(self, package_ids):
        """获取指定表情包详情"""
        headers = {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(GET_EMOTICON_PACKAGE_API, 
                                   params={"business": "reply", "ids": ",".join(map(str, package_ids))}, 
                                   headers=headers, 
                                   timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == 0:
                return data["data"]["packages"]
            else:
                print(f"获取表情包详情失败: {data['message']}")
                return []
        except Exception as e:
            print(f"获取表情包详情异常: {str(e)}")
            return []
    
    def get_live_emoticons(self, room_id):
        """获取直播间表情包"""
        headers = {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(GET_LIVE_EMOTICON_API, 
                                   params={"platform": "android", "room_id": room_id}, 
                                   headers=headers, 
                                   timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == 0:
                return data["data"]["data"]
            else:
                print(f"获取直播间表情包失败: {data['message']}")
                return []
        except Exception as e:
            print(f"获取直播间表情包异常: {str(e)}")
            return []
        
    def get_UP_UID(self, room_id):
        """获取直播间UP的UID"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(GET_LIVE_INFORMATION, 
                                   params={"room_id": room_id}, 
                                   headers=headers, 
                                   timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == 0:
                return data["data"]["uid"]
            else:
                print(f"获取主播UID失败: {data['message']}")
                return []
        except Exception as e:
            print(f"获取主播UID异常: {str(e)}")
            return []
        
    def get_charge_emoticons(self, mid):
        """获取充电表情包"""
        headers = {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(GET_CHARGE_EMOTICON_API, 
                                   params={"up_mid": mid}, 
                                   headers=headers, 
                                   timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == 0:
                data_name = data["data"]["up"]["name"]
                data_type = { str(i['privilege_type']):i['privilege_name'] for i in data["data"]["up"]["tabs"] if i.get('locked')}
                data_list = {data_name:data_type}
                data = data["data"]["privilege_rights"]
                result = {str(k): data[str(k)] for k in data_type if str(k) in data}
                return data_list, result
            elif data["code"] == 203010:
                return None,{}
            else:
                print(f"获取主播充电表情包失败: {data['message']}")
                return None,{}
        except Exception as e:
            print(f"获取主播充电表情包异常: {str(e)}")
            return None,{}
    
    def load_all_emoticons(self, room_id):
        """加载所有表情包（用户表情+直播间表情）"""
        self.emoticons.clear()
        
        # 获取用户表情包
        user_packages = self.get_user_emoticons()
        for pkg in user_packages:
            pkg_id = pkg["id"]
            if pkg_id not in self.emoticons:
                self.emoticons[pkg_id] = {
                    "name": pkg["text"],
                    "type": "user",
                    "emotes": []
                }
            
            # 获取表情包详情
            details = self.get_emoticon_package([pkg_id])
            if details:
                for emoticon in details[0]["emote"]:
                    self.emoticons[pkg_id]["emotes"].append({
                        "name": emoticon["text"],
                        "url": emoticon["url"],
                        "id": emoticon["id"]
                    })
        
        # 获取直播间表情包
        live_packages = self.get_live_emoticons(room_id)
        for pkg in live_packages:
            pkg_id = pkg["pkg_id"]
            if pkg_id not in self.emoticons:
                self.emoticons[pkg_id] = {
                    "name": pkg["pkg_name"],
                    "type": "live",
                    "emotes": []
                }
            
            for emoticon in pkg["emoticons"]:
                self.emoticons[pkg_id]["emotes"].append({
                    "name": emoticon["emoji"],
                    "url": emoticon["url"],
                    "id": emoticon.get("emoticon_unique", "")
                })

        # 获取充电表情包
        live_packages = {}
        # up_uid = 3546638935132603
        up_uid = self.get_UP_UID(room_id)
        charge_type, charge_packages = self.get_charge_emoticons(up_uid)
        for pkg_num,pkg in charge_packages.items():
            if not pkg.get('emote',{}).get('locked',None):
                continue
            pkg_id = up_uid
            name = list(charge_type.keys())[0]
            charge_dirt = charge_type[name]
            if (pkg_id not in self.emoticons) or (self.emoticons.get(pkg_id).get('num') != pkg_num):
                self.emoticons[pkg_id] = {
                    "name": f"{name}-[{charge_dirt[pkg_num]}]",
                    "type": "upower",
                    "emotes": [],
                    "num": pkg_num
                }
            
            for emoticon in pkg.get('emote',{}).get('emojis'):
                self.emoticons[pkg_id]["emotes"].append({
                    "name": f"upower_[UPOWER_{pkg_id}_{emoticon['name']}]",
                    "url": emoticon["icon"],
                    "id": emoticon['id']
                })
        
        return self.emoticons
    
    def send_emoticon(self, room_id, emoticon_data):
        """发送表情"""
        headers = {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        csrf_token = self.get_csrf_from_cookie()
        
        #判断表情类型并构建消息
        if emoticon_data["type"] == "upower":
            msg = emoticon_data["name"]  # 用户表情直接使用名称
        else:
            msg = f"{emoticon_data['id']}"  # 直播间表情使用特殊格式
        
        payload = {
            "csrf": csrf_token,
            "csrf_token": csrf_token,
            "roomid": room_id,
            "msg": msg,
            "rnd": int(time.time()),
            "fontsize": 25,
            "color": 16777215,
            "mode": 1,
            "dm_type": 1,
            "emoticonOptions": '[object Object]',
            "room_type": 0,
            "jumpfrom": 0
        }
        
        try:
            response = requests.post(SEND_DANMU_API, headers=headers, data=payload)
            result = response.json()
            
            return result.get("code") == 0, result.get("message", "未知错误")
        except Exception as e:
            return False, str(e)


class EmoticonButton(QPushButton):
    """表情按钮控件"""
    clicked_with_data = pyqtSignal(dict)
    
    def __init__(self, emoticon_data, parent=None):
        super().__init__(parent)
        self.emoticon_data = emoticon_data
        
        # 设置按钮大小
        self.setFixedSize(64, 64)
        self.setIconSize(QSize(48, 48))
        
        # 异步加载图片
        self.load_image()
        
        # 设置提示
        self.setToolTip(emoticon_data["name"])
        
        # 连接点击事件
        self.clicked.connect(self.on_click)
    
    def load_image(self):
        """异步加载表情图片"""
        # 这里可以使用线程池或QNetworkAccessManager实现异步加载
        # 简化实现：直接同步加载
        try:
            response = requests.get(self.emoticon_data["url"], timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.setIcon(QIcon(pixmap))
        except:
            # 加载失败使用默认图标
            self.setText(self.emoticon_data["name"][:4])
    
    def on_click(self):
        """按钮点击事件"""
        self.clicked_with_data.emit(self.emoticon_data)


class EmoticonPackageWidget(QWidget):
    """表情包展示控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.emoticon_buttons = []
    
    def set_emoticons(self, emoticons):
        """设置表情列表"""
        # 清除现有表情
        for button in self.emoticon_buttons:
            self.layout.removeWidget(button)
            button.deleteLater()
        self.emoticon_buttons.clear()
        
        # 添加新表情
        row, col = 0, 0
        max_cols = 5  # 每行最多5个表情
        
        for emoticon in emoticons:
            button = EmoticonButton(emoticon, self)
            self.layout.addWidget(button, row, col)
            self.emoticon_buttons.append(button)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.emoticon_manager = EmoticonManager()
        self.current_room_id = DEFAULT_ROOM_ID
        self.sending_timer = QTimer()
        self.sending_timer.timeout.connect(self.send_next_emoticon)
        self.send_queue = []
        self.is_sending = False
        
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Bilibili直播表情包发送机")
        self.setGeometry(100, 100, 1200, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 添加配置区域
        self.create_config_widget()
        main_layout.addWidget(self.config_widget)
        
        # 内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        
        # 左侧表情包列表
        left_frame = QFrame()
        left_frame.setFixedWidth(200)
        left_layout = QVBoxLayout(left_frame)
        
        left_layout.addWidget(QLabel("表情包列表"))
        self.package_list = QListWidget()
        self.package_list.currentRowChanged.connect(self.on_package_selected)
        left_layout.addWidget(self.package_list)
        
        # 右侧表情展示区
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        
        right_layout.addWidget(QLabel("表情展示"))
        self.emoticon_widget = EmoticonPackageWidget()
        
        # 添加滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.emoticon_widget)
        scroll_area.setWidgetResizable(True)
        right_layout.addWidget(scroll_area)
        
        # 添加到内容布局
        content_layout.addWidget(left_frame)
        content_layout.addWidget(right_frame)
        
        # 添加到主布局
        main_layout.addWidget(content_widget)
    
    def create_config_widget(self):
        """创建配置部件"""
        self.config_widget = QWidget()
        config_layout = QVBoxLayout(self.config_widget)
        
        # 第一行配置
        row1_layout = QHBoxLayout()
        row1_layout.addWidget(QLabel("直播间ID:"))
        self.room_id_edit = QLineEdit(str(DEFAULT_ROOM_ID))
        row1_layout.addWidget(self.room_id_edit)
        
        row1_layout.addWidget(QLabel("Cookie:"))
        self.cookie_edit = QLineEdit(DEFAULT_COOKIE)
        self.cookie_edit.setEchoMode(QLineEdit.Password)
        row1_layout.addWidget(self.cookie_edit)
        
        self.load_emoticons_btn = QPushButton("加载表情包")
        self.load_emoticons_btn.clicked.connect(self.load_emoticons)
        row1_layout.addWidget(self.load_emoticons_btn)
        
        config_layout.addLayout(row1_layout)
        
        # 第二行配置
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(QLabel("发送间隔(秒):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)
        self.interval_spin.setValue(10)
        row2_layout.addWidget(self.interval_spin)
        
        self.loop_check = QCheckBox("循环发送")
        row2_layout.addWidget(self.loop_check)
        
        self.start_btn = QPushButton("开始发送")
        self.start_btn.clicked.connect(self.toggle_sending)
        row2_layout.addWidget(self.start_btn)
        
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.clicked.connect(self.save_config)
        row2_layout.addWidget(self.save_config_btn)
        
        config_layout.addLayout(row2_layout)
    
    def load_config(self):
        """加载配置"""
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.room_id_edit.setText(str(config.get("room_id", DEFAULT_ROOM_ID)))
                self.cookie_edit.setText(config.get("cookie", DEFAULT_COOKIE))
                self.interval_spin.setValue(config.get("interval", 10))
                self.loop_check.setChecked(config.get("loop", False))
        except:
            pass  # 如果配置文件不存在，使用默认值
    
    def save_config(self):
        """保存配置"""
        config = {
            "room_id": int(self.room_id_edit.text()),
            "cookie": self.cookie_edit.text(),
            "interval": self.interval_spin.value(),
            "loop": self.loop_check.isChecked()
        }
        
        try:
            with open("config.json", "w") as f:
                json.dump(config, f)
            QMessageBox.information(self, "成功", "配置已保存")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存配置失败: {str(e)}")
    
    def load_emoticons(self):
        """加载表情包"""
        room_id = int(self.room_id_edit.text())
        cookie = self.cookie_edit.text()
        
        if not cookie:
            QMessageBox.warning(self, "错误", "请先填写Cookie")
            return
        
        self.emoticon_manager.set_cookie(cookie)
        self.current_room_id = room_id
        
        try:
            emoticons = self.emoticon_manager.load_all_emoticons(room_id)
            self.populate_package_list(emoticons)
            QMessageBox.information(self, "成功", f"已加载 {len(emoticons)} 个表情包")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载表情包失败: {str(e)}")
    
    def populate_package_list(self, emoticons):
        """填充表情包列表"""
        self.package_list.clear()
        
        for pkg_id, pkg_data in emoticons.items():
            item = QListWidgetItem(pkg_data["name"])
            item.setData(Qt.UserRole, pkg_id)  # 存储表情包ID
            self.package_list.addItem(item)
    
    def on_package_selected(self, row):
        """表情包选择事件"""
        if row < 0:
            return
        
        item = self.package_list.item(row)
        pkg_id = item.data(Qt.UserRole)
        pkg_data = self.emoticon_manager.emoticons.get(pkg_id)
        
        if pkg_data:
            # 为每个表情添加类型信息
            emoticons_with_type = []
            for emoticon in pkg_data["emotes"]:
                emoticon_with_type = emoticon.copy()
                emoticon_with_type["type"] = pkg_data["type"]
                emoticons_with_type.append(emoticon_with_type)
            
            self.emoticon_widget.set_emoticons(emoticons_with_type)
            
            # 连接表情点击事件
            for button in self.emoticon_widget.emoticon_buttons:
                try:
                    button.clicked_with_data.disconnect()
                except:
                    pass
                button.clicked_with_data.connect(self.on_emoticon_clicked)
    
    def on_emoticon_clicked(self, emoticon_data):
        """表情点击事件"""
        if self.is_sending:
            # 如果正在发送，添加到队列
            self.send_queue.append(emoticon_data)
        else:
            # 直接发送
            success, message = self.emoticon_manager.send_emoticon(self.current_room_id, emoticon_data)
            status = "成功" if success else "失败"
            self.statusBar().showMessage(f"发送{status}: {message}", 3000)
    
    def toggle_sending(self):
        """切换发送状态"""
        if self.is_sending:
            self.stop_sending()
        else:
            self.start_sending()
    
    def start_sending(self):
        """开始发送"""
        if not self.send_queue:
            QMessageBox.warning(self, "提示", "请先点击要发送的表情")
            return
        
        self.is_sending = True
        self.start_btn.setText("停止发送")
        self.sending_timer.start(self.interval_spin.value() * 1000)
    
    def stop_sending(self):
        """停止发送"""
        self.is_sending = False
        self.start_btn.setText("开始发送")
        self.sending_timer.stop()
    
    def send_next_emoticon(self):
        """发送下一个表情"""
        if not self.send_queue:
            self.stop_sending()
            return
        
        emoticon_data = self.send_queue[0]
        success, message = self.emoticon_manager.send_emoticon(self.current_room_id, emoticon_data)
        
        if not self.loop_check.isChecked():
            self.send_queue.pop(0)
        
        status = "成功" if success else "失败"
        self.statusBar().showMessage(f"发送{status}: {message}", 3000)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 应用现代样式
    qtmodern.styles.dark(app)
    
    window = MainWindow()
    modern_window = qtmodern.windows.ModernWindow(window)
    modern_window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()