# app/config.py
# Default Configuration
DEFAULT_COOKIE = "" # 默认cookie为空
DEFAULT_ROOM_ID = 31586244

# API Endpoints
GET_USER_EMOTICON_API = "https://api.bilibili.com/x/emote/user/panel/web"
GET_EMOTICON_PACKAGE_API = "https://api.bilibili.com/x/emote/package"
GET_LIVE_EMOTICON_API = "https://api.live.bilibili.com/xlive/web-ucenter/v2/emoticon/GetEmoticons"
SEND_DANMU_API = "https://api.live.bilibili.com/msg/send"
GET_CHARGE_EMOTICON_API = "https://api.bilibili.com/x/upowerv2/gw/rights/index"
GET_LIVE_INFORMATION = "https://api.live.bilibili.com/room/v1/Room/get_info"
GET_UP_INFORMATION = "https://api.live.bilibili.com/live_user/v1/Master/info"

# Cache directories
CACHE_DIR = "cache"
IMAGE_CACHE_DIR = f"{CACHE_DIR}/images"
DATA_CACHE_DIR = f"{CACHE_DIR}/data"

ICON_SIZE = 84

# Download manager settings
MAX_DOWNLOAD_THREADS = 4  # 最大并发下载线程数