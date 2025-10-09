# app/models.py
import requests
import time
import os
import json
import logging
import threading
from queue import Queue
from collections import defaultdict
from typing import List, Dict, Union, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

# 从同级目录的 config.py 中导入配置
from . import config
from .download_manager import DownloadManager

class EmoticonManager(QObject):
    """
    模型层 (Model): 负责处理所有与Bilibili API交互、数据获取、处理和缓存的逻辑。
    这一层不涉及任何UI操作。
    """
    # 信号：下载完成时发出
    download_completed = pyqtSignal(str, str, str)  # url, emoticon_id, local_path
    download_failed = pyqtSignal(str, str, str)     # url, emoticon_id, error_message

    def __init__(self):
        super().__init__()
        self.emoticons = {}  # 内存中存储当前加载的表情包数据
        self.cookie = config.DEFAULT_COOKIE
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.download_manager = None  # 下载管理器

        # 批量映射更新系统
        self._pending_mappings = defaultdict(dict)  # 待处理的映射更新 {mapping_file: {emoticon_id: package_name}}
        self._mapping_lock = threading.Lock()  # 映射更新锁
        self._batch_timer = None  # 批量写入定时器
        self._batch_delay = 2.0  # 批量写入延迟时间（秒）

        # 房间号-UID-名称缓存系统
        self._room_cache_file = os.path.join(config.DATA_CACHE_DIR, "room_cache.json")
        self._room_cache = {}  # 内存缓存 {room_id: {"uid": uid, "name": name}}
        self._room_cache_lock = threading.Lock()  # 缓存锁

        self._setup_cache()
        self._load_room_cache()

    def _setup_cache(self):
        """创建缓存目录（如果不存在）。"""
        os.makedirs(config.IMAGE_CACHE_DIR, exist_ok=True)
        os.makedirs(config.DATA_CACHE_DIR, exist_ok=True)
        # 创建映射文件目录
        os.makedirs(os.path.join(config.DATA_CACHE_DIR, "mappings"), exist_ok=True)
        logging.info("缓存目录已准备就绪。")

    def _load_room_cache(self):
        """
        从文件加载房间号-UID-名称缓存。
        """
        try:
            if os.path.exists(self._room_cache_file):
                with open(self._room_cache_file, 'r', encoding='utf-8') as f:
                    self._room_cache = json.load(f)
                logging.info(f"房间缓存已加载，共 {len(self._room_cache)} 条记录")
            else:
                logging.info("房间缓存文件不存在，将创建新缓存")
        except Exception as e:
            logging.error(f"加载房间缓存失败: {e}")
            self._room_cache = {}

    def _save_room_cache(self):
        """
        保存房间号-UID-名称缓存到文件。
        """
        try:
            with open(self._room_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._room_cache, f, ensure_ascii=False, indent=2)
            logging.debug(f"房间缓存已保存，共 {len(self._room_cache)} 条记录")
        except Exception as e:
            logging.error(f"保存房间缓存失败: {e}")

    def _update_room_cache(self, room_id: int, uid: int, name: str):
        """
        更新房间号-UID-名称缓存。

        Args:
            room_id: 房间号
            uid: 主播UID
            name: 主播名称
        """
        with self._room_cache_lock:
            room_id_str = str(room_id)
            self._room_cache[room_id_str] = {
                "uid": uid,
                "name": name
            }
            self._save_room_cache()

    def _get_cached_room_info(self, room_id: int) -> Tuple[Union[int, None], Union[str, None]]:
        """
        从缓存中获取房间信息。

        Args:
            room_id: 房间号

        Returns:
            (uid, name) 元组，如果缓存中没有则返回 (None, None)
        """
        room_id_str = str(room_id)
        with self._room_cache_lock:
            if room_id_str in self._room_cache:
                cache_data = self._room_cache[room_id_str]
                return cache_data.get("uid"), cache_data.get("name")
        return None, None

    def get_cached_rooms(self) -> List[Dict[str, str]]:
        """
        获取所有缓存的房间信息，用于下拉选择框。

        Returns:
            房间信息列表，每个元素包含 room_id 和 name
        """
        with self._room_cache_lock:
            rooms = []
            for room_id_str, cache_data in self._room_cache.items():
                if cache_data.get("name"):  # 只返回有名称的房间
                    rooms.append({
                        "room_id": room_id_str,
                        "name": cache_data["name"]
                    })
            # 按房间ID排序
            rooms.sort(key=lambda x: int(x["room_id"]))
            return rooms

    def _schedule_batch_write(self):
        """
        安排批量写入操作。
        """
        if self._batch_timer is not None:
            self._batch_timer.cancel()

        self._batch_timer = threading.Timer(self._batch_delay, self._flush_pending_mappings)
        self._batch_timer.daemon = True
        self._batch_timer.start()

    def _flush_pending_mappings(self):
        """
        批量写入所有待处理的映射更新。
        """
        with self._mapping_lock:
            if not self._pending_mappings:
                return

            pending_copy = self._pending_mappings.copy()
            self._pending_mappings.clear()

        # 批量写入所有映射文件
        for mapping_file, updates in pending_copy.items():
            self._batch_update_mapping_file(mapping_file, updates)

    def _batch_update_mapping_file(self, mapping_file: str, updates: Dict[str, str]):
        """
        批量更新映射文件，合并所有更新操作。

        Args:
            mapping_file: 映射文件路径
            updates: 要更新的映射 {emoticon_id: package_name}
        """
        try:
            # 读取现有映射
            existing_mappings = {}
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    existing_mappings = json.load(f)

            # 合并更新（新值覆盖旧值）
            existing_mappings.update(updates)

            # 写入合并后的映射
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(existing_mappings, f, ensure_ascii=False, indent=2)

            logging.debug(f"批量更新映射文件 {mapping_file}: {len(updates)} 个更新")
        except Exception as e:
            logging.error(f"批量更新映射文件失败 {mapping_file}: {e}")
            # 如果失败，将更新重新加入待处理队列
            with self._mapping_lock:
                self._pending_mappings[mapping_file].update(updates)

    def _get_sanitized_package_name(self, package_name: str) -> str:
        """
        清理表情包名称，移除非法文件名字符。
        """
        # 移除Windows文件名中不允许的字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            package_name = package_name.replace(char, '_')
        # 限制长度避免路径过长
        return package_name[:100]

    def _get_package_cache_dir(self, package_name: str) -> str:
        """
        获取表情包的缓存目录路径。
        """
        sanitized_name = self._get_sanitized_package_name(package_name)
        return os.path.join(config.IMAGE_CACHE_DIR, sanitized_name)

    def _get_mapping_file_path(self, package_name: str) -> str:
        """
        获取表情包ID-名称映射文件的路径。
        """
        sanitized_name = self._get_sanitized_package_name(package_name)
        return os.path.join(config.DATA_CACHE_DIR, "mappings", f"{sanitized_name}.json")

    def set_cookie(self, cookie: str):
        """设置请求时使用的Cookie。"""
        self.cookie = cookie

    def init_download_manager(self, max_threads: int = 4):
        """初始化下载管理器"""
        if self.download_manager:
            self.download_manager.shutdown()

        self.download_manager = DownloadManager(self, max_threads)
        # 连接下载管理器的信号到模型的信号
        self.download_manager.download_completed.connect(self.download_completed)
        self.download_manager.download_failed.connect(self.download_failed)
        logging.info(f"下载管理器已初始化，最大工作线程数: {max_threads}")

    def get_csrf_from_cookie(self) -> str:
        """从Cookie字符串中提取bili_jct (csrf_token)。"""
        try:
            cookie_dict = {pair.split('=', 1)[0].strip(): pair.split('=', 1)[1] for pair in self.cookie.split(';') if '=' in pair}
            return cookie_dict.get('bili_jct', '')
        except Exception as e:
            logging.error(f"从Cookie中解析CSRF失败: {e}")
            return ''

    def get_emoticon_image(self, url: str, emoticon_id, package_name: str = None) -> str:
        """
        获取表情图片。如果本地有缓存，则返回本地路径，否则使用下载管理器下载。
        返回本地文件的绝对路径。
        """
        # 从URL中获取文件扩展名，如果没有则默认为.png
        file_extension = os.path.splitext(url)[1]
        if not file_extension:
            file_extension = ".png"

        # 统一ID格式为字符串，避免路径问题
        emoticon_id_str = str(emoticon_id).replace(":", "_").replace("/", "_")

        # 如果没有提供包名
        if not package_name:
            raise ValueError(f"表情包缺失包名,ID:{emoticon_id}")

        # 使用新的缓存系统
        return self._get_emoticon_image_with_package(url, emoticon_id_str, file_extension, package_name)

    def _get_emoticon_image_with_package(self, url: str, emoticon_id_str: str, file_extension: str, package_name: str) -> str:
        """
        使用表情包分类的缓存系统获取表情图片。
        """
        # 获取表情包缓存目录
        package_cache_dir = self._get_package_cache_dir(package_name)
        os.makedirs(package_cache_dir, exist_ok=True)

        # 新的缓存文件路径：ID+包名
        sanitized_package_name = self._get_sanitized_package_name(package_name)
        local_path = os.path.join(package_cache_dir, f"{emoticon_id_str}_{sanitized_package_name}{file_extension}")

        # 检查映射文件，判断是否需要刷新缓存
        mapping_file = self._get_mapping_file_path(package_name)
        should_refresh = self._should_refresh_cache(mapping_file, emoticon_id_str, package_name)

        if os.path.exists(local_path) and not should_refresh:
            logging.debug(f"图片在缓存中找到: {local_path}")
            return local_path

        # 如果没有下载管理器，使用同步下载
        if not self.download_manager:
            logging.info(f"正在下载图片: {url}")
            try:
                response = requests.get(url, timeout=10, headers={"User-Agent": self.user_agent})
                response.raise_for_status()
                with open(local_path, 'wb') as f:
                    f.write(response.content)

                # 更新映射文件
                self._update_mapping_file(mapping_file, emoticon_id_str, package_name)

                logging.info(f"图片已下载并缓存至: {local_path}")
                return local_path
            except requests.RequestException as e:
                logging.error(f"下载图片失败 {url}: {e}")
                return "" # 下载失败返回空字符串
        else:
            # 使用下载管理器异步下载
            if self.download_manager.add_download_task(local_path ,url, emoticon_id_str, package_name, priority=0):
                # 更新映射文件
                self._update_mapping_file(mapping_file, emoticon_id_str, package_name)
                logging.debug(f"已添加下载任务: {url}")
            return ""  # 异步下载，暂时返回空路径

    # --- 以下是所有与Bilibili API交互的方法 ---

    def get_user_emoticons(self) -> List[Dict]:
        """获取用户表情包列表 (带缓存)。"""
        headers = {"Cookie": self.cookie, "User-Agent": self.user_agent}
        try:
            response = requests.get(config.GET_USER_EMOTICON_API, params={"business": "reply"}, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data["code"] == 0:
                logging.info("成功获取用户表情包列表。")
                return data["data"]["packages"]
            else:
                logging.error(f"获取用户表情包失败: {data['message']}")
                return []
        except Exception as e:
            logging.error(f"获取用户表情包异常: {e}")
            return []

    def get_emoticon_package(self, package_ids: List[int]) -> List[Dict]:
        """获取指定表情包的详细信息 (带缓存)。"""
        headers = {"Cookie": self.cookie, "User-Agent": self.user_agent}
        try:
            response = requests.get(config.GET_EMOTICON_PACKAGE_API, params={"business": "reply", "ids": ",".join(map(str, package_ids))}, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data["code"] == 0:
                logging.info(f"成功获取表情包详情: {package_ids}")
                return data["data"]["packages"]
            else:
                logging.error(f"获取表情包详情失败: {data['message']}")
                return []
        except Exception as e:
            logging.error(f"获取表情包详情异常: {e}")
            return []

    def get_live_emoticons(self, room_id: int) -> List[Dict]:
        """获取直播间表情包 (带缓存)。"""
        headers = {"Cookie": self.cookie, "User-Agent": self.user_agent}
        try:
            response = requests.get(config.GET_LIVE_EMOTICON_API, params={"platform": "android", "room_id": room_id}, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data["code"] == 0:
                logging.info(f"成功获取直播间 {room_id} 的表情包。")
                return data["data"]["data"]
            else:
                logging.error(f"获取直播间表情包失败: {data['message']}")
                return []
        except Exception as e:
            logging.error(f"获取直播间表情包异常: {e}")
            return []

    def get_UP_UID(self, room_id: int) -> int:
        """获取直播间主播的UID (带缓存)。"""
        # 首先尝试从缓存获取
        cached_uid, cached_name = self._get_cached_room_info(room_id)
        if cached_uid is not None:
            logging.debug(f"从缓存获取房间 {room_id} 的主播UID: {cached_uid}")
            return cached_uid

        # 缓存中没有，从API获取
        headers = {"User-Agent": self.user_agent}
        try:
            response = requests.get(config.GET_LIVE_INFORMATION, params={"room_id": room_id}, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data["code"] == 0:
                uid = data["data"]["uid"]
                logging.info(f"成功获取房间 {room_id} 的主播UID: {uid}")

                # 获取主播名称并更新缓存
                up_name = self._get_up_name_from_api(uid)
                if up_name:
                    self._update_room_cache(room_id, uid, up_name)

                return uid
            else:
                logging.error(f"获取主播UID失败: {data['message']}")
                return 0
        except Exception as e:
            logging.error(f"获取主播UID异常: {e}")
            return 0

    def get_charge_emoticons(self, mid: int) -> Tuple[Union[Dict, None], Dict]:
        """获取充电专属表情包 (带缓存)。"""
        headers = {"Cookie": self.cookie, "User-Agent": self.user_agent}
        try:
            response = requests.get(config.GET_CHARGE_EMOTICON_API, params={"up_mid": mid}, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == 0:
                data_name = data["data"]["up"]["name"]
                # 过滤出已解锁的充电包类型
                data_type = {str(i['privilege_type']): i['privilege_name'] for i in data["data"]["up"]["tabs"] if not i.get('locked')}
                data_list = {data_name: data_type}
                privilege_rights = data["data"]["privilege_rights"]
                # 筛选出已解锁的表情包详情
                result = {str(k): privilege_rights[str(k)] for k in data_type if str(k) in privilege_rights and not privilege_rights[str(k)].get('emote', {}).get('locked')}
                logging.info(f"成功获取主播 {mid} 的充电表情包。")
                return data_list, result
            elif data["code"] == 203010:
                logging.warning(f"主播 {mid} 没有充电专属表情包。")
                return None, {}
            else:
                logging.error(f"获取主播充电表情包失败: {data['message']}")
                return None, {}
        except Exception as e:
            logging.error(f"获取主播充电表情包异常: {e}")
            return None, {}

    def _get_up_name_from_api(self, uid: int) -> str:
        """
        通过UID从API获取主播名称。

        Args:
            uid: 主播UID

        Returns:
            主播名称，如果获取失败则返回空字符串
        """
        headers = {"User-Agent": self.user_agent}
        try:
            response = requests.get(config.GET_UP_INFORMATION, params={"uid": uid}, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data["code"] == 0:
                up_name = data["data"]["info"]["uname"]
                logging.info(f"成功获取主播 {uid} 的名称: {up_name}")
                return up_name
            else:
                logging.warning(f"获取主播名称失败: {data['message']}")
                return ""
        except Exception as e:
            logging.error(f"获取主播名称异常: {e}")
            return ""

    def _get_up_name_from_room(self, room_id: int) -> str:
        """
        获取直播间UP主名称。
        如果无法获取UP主名称，则返回直播间ID作为备用。
        """
        # 首先尝试从缓存获取
        cached_uid, cached_name = self._get_cached_room_info(room_id)
        if cached_name is not None:
            logging.debug(f"从缓存获取房间 {room_id} 的主播名称: {cached_name}")
            return cached_name

        # 缓存中没有名称，但可能有UID
        if cached_uid is not None:
            # 有UID但没有名称，通过API获取名称
            up_name = self._get_up_name_from_api(cached_uid)
            if up_name:
                self._update_room_cache(room_id, cached_uid, up_name)
                return up_name

        # 缓存中什么都没有，通过常规流程获取
        try:
            up_UID = self.get_UP_UID(room_id)
            if up_UID:
                up_name = self._get_up_name_from_api(up_UID)
                if up_name:
                    return up_name
        except Exception as e:
            logging.error(f"获取主播名称异常，使用房间ID: {room_id}, 错误: {e}")

        # 所有方法都失败，返回房间ID
        logging.warning(f"获取主播名称失败，使用房间ID: {room_id}")
        return str(room_id)

    def _apply_special_package_renaming(self, package_name: str, package_type: str, room_id: int, up_name: str = None) -> str:
        """
        应用特殊表情包重命名规则。

        Args:
            package_name: 原始表情包名称
            package_type: 表情包类型
            room_id: 直播间ID
            up_name: UP主名称（可选）
        """
        if not up_name:
            up_name = self._get_up_name_from_room(room_id)

        # 特殊表情包重命名规则
        special_names = {
            "UP主大表情": f"{up_name}大表情",
            "房间专属表情": f"{up_name}房间专属表情",
            "为TA充电": f"{up_name}充电表情"
        }

        # 检查是否为特殊表情包
        for original_name, new_name in special_names.items():
            if original_name in package_name:
                return new_name

        # 对于充电表情包的特殊处理
        if package_type == "upower" and "为TA充电" in package_name:
            return f"{up_name}充电表情"

        return package_name

    def load_all_emoticons(self, room_id: int) -> Dict:
        """
        核心方法：加载并整合所有类型的表情包（用户、直播间、充电）。
        这个方法会被 Controller 在后台线程中调用。
        """
        self.emoticons.clear()

        # 获取UP主名称用于特殊表情包重命名
        up_name = self._get_up_name_from_room(room_id)

        # 1. 获取用户表情包
        user_packages = self.get_user_emoticons()
        if user_packages:
            user_pkg_ids = [pkg['id'] for pkg in user_packages]
            details = self.get_emoticon_package(user_pkg_ids)
            if details:
                details_map = {pkg['id']: pkg for pkg in details}
                for pkg in user_packages:
                    pkg_id = pkg["id"]
                    detail_pkg = details_map.get(pkg_id)
                    if detail_pkg and detail_pkg.get("emote"):
                        # 应用重命名规则
                        original_name = pkg["text"]
                        renamed_name = self._apply_special_package_renaming(original_name, "user", room_id, up_name)

                        self.emoticons[pkg_id] = {
                            "name": renamed_name,
                            "type": "user",
                            "emotes": [{"name": e["text"], "url": e["url"], "id": e["id"]} for e in detail_pkg["emote"]]
                        }

        # 2. 获取直播间表情包
        live_packages = self.get_live_emoticons(room_id)
        for pkg in live_packages:
            pkg_id = pkg["pkg_id"] # 不需要避免冲突,这个表情包列表只是为了补全房间表情的
            if pkg_id not in self.emoticons:
                # 应用重命名规则
                original_name = pkg["pkg_name"]
                renamed_name = self._apply_special_package_renaming(original_name, "live", room_id, up_name)

                self.emoticons[pkg_id] = {
                    "name": renamed_name,
                    "type": "live",
                    "emotes": [{"name": e["emoji"], "url": e["url"], "id": e.get("emoticon_unique", "")} for e in pkg["emoticons"]]
                }

        # 3. 获取充电表情包
        up_uid = self.get_UP_UID(room_id)
        if up_uid:
            charge_type_map, charge_packages = self.get_charge_emoticons(up_uid)
            if charge_type_map and charge_packages:
                charge_up_name = list(charge_type_map.keys())[0]
                charge_level_names = list(charge_type_map.values())[0]

                for pkg_num_str, pkg_data in charge_packages.items():
                    # 为充电包创建唯一的ID
                    pkg_id = f"upower_{up_uid}_{pkg_num_str}"
                    level_name = charge_level_names.get(pkg_num_str, f"Level {pkg_num_str}")

                    # 应用重命名规则
                    original_name = f"{charge_up_name}-[{level_name}]"
                    renamed_name = self._apply_special_package_renaming(original_name, "upower", room_id, up_name)

                    self.emoticons[pkg_id] = {
                        "name": renamed_name,
                        "type": "upower",
                        "emotes": []
                    }
                    for e in pkg_data.get('emote', {}).get('emojis', []):
                         self.emoticons[pkg_id]["emotes"].append({
                            # 充电表情的发送格式是特殊的
                            "name": f"upower_[UPOWER_{up_uid}_{e['name']}]",
                            "url": e["icon"],
                            "id": e['id']
                        })

        logging.info(f"所有表情包加载完成，共 {len(self.emoticons)} 个包。")
        return self.emoticons

    def send_emoticon(self, room_id: int, emoticon_data: Dict) -> Tuple[bool, str]:
        """
        发送表情弹幕到指定直播间。
        """
        headers = {"Cookie": self.cookie, "User-Agent": self.user_agent}
        csrf_token = self.get_csrf_from_cookie()
        if not csrf_token:
            return False, "无法获取CSRF Token，请检查Cookie"

        # 根据表情类型构建消息内容
        if emoticon_data["type"] == "upower":
            msg = emoticon_data["name"]  # 充电表情直接使用特殊格式的名称
        elif emoticon_data["type"] == "live":
            msg = f"{emoticon_data['id']}" # 直播间表情使用ID代码
        else:
            msg = f"upower_{emoticon_data['name']}" # 普通表情使用文字代码

        payload = {
            "bubble": 0,
            "msg": msg,
            "color": 16777215,
            "fontsize": 25,
            "mode": 1,
            "roomid": room_id,
            "csrf": csrf_token,
            "csrf_token": csrf_token,
            "rnd": int(time.time())
        }
        
        # 对于直播间和充电表情，需要额外附加dm_type和emoticonOptions
        if emoticon_data['type'] in ['live', 'upower','user']:
            payload['dm_type'] = 1
            # 构建emoticonOptions的JSON字符串
            options = {
                "bulge_display": 0,
                "emoticon_unique": emoticon_data['id'],
                "url": emoticon_data['url'],
                "is_dynamic": 1
            }
            payload['emoticon_options'] = json.dumps(options, ensure_ascii=False)

        logging.info(f"准备发送表情: {msg} 到房间 {room_id}")
        try:
            response = requests.post(config.SEND_DANMU_API, headers=headers, data=payload)
            result = response.json()
            logging.info(f"发送响应: {result}")
            
            if result.get("code") == 0:
                return True, result.get("message", "发送成功")
            else:
                return False, result.get("message", "未知错误")
        except Exception as e:
            logging.error(f"发送表情时发生异常: {e}")
            return False, str(e)

    def _should_refresh_cache(self, mapping_file: str, emoticon_id: str, current_package_name: str) -> bool:
        """
        检查是否需要刷新缓存。
        如果表情包名称发生变化，则需要刷新缓存。
        """
        if not os.path.exists(mapping_file):
            return False

        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)

            # 检查该表情ID对应的包名是否与当前包名一致
            if emoticon_id in mappings:
                cached_package_name = mappings[emoticon_id]
                if cached_package_name != current_package_name:
                    logging.info(f"检测到表情包名称变化: {cached_package_name} -> {current_package_name}，需要刷新缓存")
                    return True

            return False
        except Exception as e:
            logging.error(f"读取映射文件失败 {mapping_file}: {e}")
            return False

    def _update_mapping_file(self, mapping_file: str, emoticon_id: str, package_name: str):
        """
        更新表情包ID-名称映射文件（使用批量更新系统）。
        """
        with self._mapping_lock:
            # 将更新添加到待处理队列
            if mapping_file not in self._pending_mappings:
                self._pending_mappings[mapping_file] = {}
            self._pending_mappings[mapping_file][emoticon_id] = package_name

        # 安排批量写入
        self._schedule_batch_write()

    def flush_all_mappings(self):
        """
        强制写入所有待处理的映射更新。
        在应用程序退出前调用此方法。
        """
        if self._batch_timer is not None:
            self._batch_timer.cancel()
            self._batch_timer = None

        self._flush_pending_mappings()
        logging.info("所有映射更新已写入完成")