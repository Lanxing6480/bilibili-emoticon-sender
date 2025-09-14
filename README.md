# B站直播表情包发送器

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

一个基于 PyQt5 开发的 Bilibili 直播表情包批量发送工具，支持快速发送、队列管理和定时发送功能。

## ✨ 特性

- 🎯 **多源表情支持** - 用户表情、直播间表情、充电专属表情
- ⚡ **双模式发送** - 快速立即发送 + 队列定时发送
- 💾 **智能缓存** - 自动缓存图片，减少网络请求
- 🎨 **现代化界面** - 深色主题，响应式布局
- 🔄 **多线程处理** - 异步加载，不阻塞UI
- 💾 **配置持久化** - 自动保存用户设置

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python main.py
```


## 📖 使用说明

1. **配置信息**
   - 输入B站直播间ID
   - 粘贴B站Cookie（开发者工具获取）
   - 点击"加载表情包"

2. **选择表情**
   - 左侧选择表情包分类
   - 中间区域显示表情预览

3. **发送模式**
   - **快速模式**：点击表情立即发送
   - **队列模式**：添加表情到队列，设置间隔时间自动发送

## 🏗️ 项目结构

```
├── app/                 # 核心代码
│   ├── models.py       # 数据模型和API处理
│   ├── views.py        # UI界面组件
│   ├── controllers.py  # 业务逻辑控制
│   ├── threads.py      # 多线程工作器
│   ├── config.py       # 配置常量
│   └── logger_setup.py # 日志配置
├── cache/              # 缓存目录
│   └── images/         # 表情图片缓存
├── main.py             # 程序入口
├── requirements.txt    # 依赖列表
└── README.md           # 项目说明
```

## 🔧 技术栈

- **Python 3.7+** - 核心编程语言
- **PyQt5** - GUI界面框架
- **requests** - HTTP网络请求

## 📊 支持的API

| 功能 | 接口地址 | 说明 |
|------|----------|------|
| 用户表情 | `api.bilibili.com/x/emote/user/panel/web` | 获取用户表情包 |
| 表情详情 | `api.bilibili.com/x/emote/package` | 获取表情包详情 |
| 直播间表情 | `api.live.bilibili.com/xlive/web-ucenter/v2/emoticon/GetEmoticons` | 获取直播间表情 |
| 充电表情 | `api.bilibili.com/x/upowerv2/gw/rights/index` | 获取充电专属表情 |
| 发送弹幕 | `api.live.bilibili.com/msg/send` | 发送表情弹幕 |

## 🎯 使用场景

- 🎪 直播互动 - 快速发送多个表情活跃气氛
- ⏰ 定时任务 - 设置定时发送配合直播内容
- 🗂️ 表情管理 - 批量管理个人表情包使用
- 🚀 效率提升 - 避免手动逐个发送的繁琐操作

## 🚧 待实现的功能和优化

1. **重复弹幕表情包时自动+1** - 监听直播间，识别重复弹幕表情包时自动"+1"
2. **直播间历史记录** - 保存常用直播间，支持快速切换
3. **UI日志面板** - 在界面中集成实时日志显示功能
4. **表情收藏功能** - 收藏常用表情快速访问
5. **发送组合预设** - 创建和保存表情发送组合

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## ⚠️ 注意事项

- 请遵守B站用户协议和相关法律法规
- 合理使用，避免滥用影响直播体验
- Cookie信息请妥善保管，注意账号安全

---

**仅供学习和交流使用，请合理使用本工具**