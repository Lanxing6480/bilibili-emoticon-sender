# app/models.py
import requests
import time
import os
import json
import logging
from typing import List, Dict, Union, Tuple

# 从同级目录的 config.py 中导入配置
from . import config

class EmoticonManager:
    """
    模型层 (Model): 负责处理所有与Bilibili API交互、数据获取、处理和缓存的逻辑。
    这一层不涉及任何UI操作。
    """
    def __init__(self):
        self.emoticons = {}  # 内存中存储当前加载的表情包数据
        self.cookie = config.DEFAULT_COOKIE
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self._setup_cache()

    def _setup_cache(self):
        """创建缓存目录（如果不存在）。"""
        os.makedirs(config.IMAGE_CACHE_DIR, exist_ok=True)
        os.makedirs(config.DATA_CACHE_DIR, exist_ok=True)
        logging.info("缓存目录已准备就绪。")

    def set_cookie(self, cookie: str):
        """设置请求时使用的Cookie。"""
        self.cookie = cookie

    def get_csrf_from_cookie(self) -> str:
        """从Cookie字符串中提取bili_jct (csrf_token)。"""
        try:
            cookie_dict = {pair.split('=', 1)[0].strip(): pair.split('=', 1)[1] for pair in self.cookie.split(';') if '=' in pair}
            return cookie_dict.get('bili_jct', '')
        except Exception as e:
            logging.error(f"从Cookie中解析CSRF失败: {e}")
            return ''

    def get_emoticon_image(self, url: str, emoticon_id) -> str:
        """
        获取表情图片。如果本地有缓存，则返回本地路径，否则下载并缓存后返回路径。
        返回本地文件的绝对路径。
        """
        # 从URL中获取文件扩展名，如果没有则默认为.png
        file_extension = os.path.splitext(url)[1]
        if not file_extension:
            file_extension = ".png"
        
        # 统一ID格式为字符串，避免路径问题
        emoticon_id_str = str(emoticon_id).replace(":", "_").replace("/", "_")
        local_path = os.path.join(config.IMAGE_CACHE_DIR, f"{emoticon_id_str}{file_extension}")

        if os.path.exists(local_path):
            logging.debug(f"图片在缓存中找到: {local_path}")
            return local_path

        logging.info(f"正在下载图片: {url}")
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
            with open(local_path, 'wb') as f:
                f.write(response.content)
            logging.info(f"图片已下载并缓存至: {local_path}")
            return local_path
        except requests.RequestException as e:
            logging.error(f"下载图片失败 {url}: {e}")
            return "" # 下载失败返回空字符串

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
        headers = {"User-Agent": self.user_agent}
        try:
            response = requests.get(config.GET_LIVE_INFORMATION, params={"room_id": room_id}, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data["code"] == 0:
                uid = data["data"]["uid"]
                logging.info(f"成功获取房间 {room_id} 的主播UID: {uid}")
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

    def load_all_emoticons(self, room_id: int) -> Dict:
        """
        核心方法：加载并整合所有类型的表情包（用户、直播间、充电）。
        这个方法会被 Controller 在后台线程中调用。
        """
        self.emoticons.clear()

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
                        self.emoticons[pkg_id] = {
                            "name": pkg["text"],
                            "type": "user",
                            "emotes": [{"name": e["text"], "url": e["url"], "id": e["id"]} for e in detail_pkg["emote"]]
                        }

        # 2. 获取直播间表情包
        live_packages = self.get_live_emoticons(room_id)
        for pkg in live_packages:
            pkg_id = pkg["pkg_id"] # 不需要避免冲突,这个表情包列表只是为了补全房间表情的
            if pkg_id not in self.emoticons:
                self.emoticons[pkg_id] = {
                    "name": pkg["pkg_name"],
                    "type": "live",
                    "emotes": [{"name": e["emoji"], "url": e["url"], "id": e.get("emoticon_unique", "")} for e in pkg["emoticons"]]
                }

        # 3. 获取充电表情包
        up_uid = self.get_UP_UID(room_id)
        if up_uid:
            charge_type_map, charge_packages = self.get_charge_emoticons(up_uid)
            if charge_type_map and charge_packages:
                up_name = list(charge_type_map.keys())[0]
                charge_level_names = list(charge_type_map.values())[0]

                for pkg_num_str, pkg_data in charge_packages.items():
                    # 为充电包创建唯一的ID
                    pkg_id = f"upower_{up_uid}_{pkg_num_str}"
                    level_name = charge_level_names.get(pkg_num_str, f"Level {pkg_num_str}")
                    
                    self.emoticons[pkg_id] = {
                        "name": f"{up_name}-[{level_name}]",
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