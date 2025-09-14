# CLAUDE.md

## 响应语言
**除非有特殊说明，请用中文回答。** (Unless otherwise specified, please respond in Chinese.)

本文档为Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是一个基于 **PyQt5 构建的 Bilibili 直播表情包发送器** 桌面应用程序。它允许用户在Bilibili直播流中发送表情包，具有自动排队和定时发送等功能。

## 架构设计

**MVC 模式**:
- `app/models.py` - 数据层（API调用、缓存、表情包管理）
- `app/views.py` - UI层（PyQt5组件和窗口）
- `app/controllers.py` - 业务逻辑层（协调模型和视图）

**核心组件**:
- `EmoticonManager` - 处理Bilibili API交互和缓存
- `MainWindow` - 主GUI界面
- `MainController` - 协调应用程序流程
- 工作线程用于异步操作

## 开发命令

**运行应用程序**:
```bash
python main.py
```

**安装依赖**:
```bash
pip install -r requirements.txt
```

**构建可执行文件**:
```bash
# 首先激活虚拟环境
venv\Scripts\activate
pyinstaller main.spec
```

**快速构建（使用批处理脚本）**:
```bash
打包.bat
```

## 项目结构

```
├── app/                 # 应用程序源代码
│   ├── models.py       # 数据模型和API交互
│   ├── views.py        # PyQt5 UI组件
│   ├── controllers.py  # 业务逻辑和协调
│   ├── threads.py      # 工作线程实现
│   ├── config.py       # 配置常量
│   └── logger_setup.py # 日志配置
├── cache/              # 缓存的表情包图片和数据
├── main.py            # 应用程序入口点
├── main.spec          # PyInstaller构建配置
├── config.json        # 用户配置（自动生成）
├── requirements.txt   # Python依赖
└── 打包.bat           # 构建脚本
```

## 关键功能特性

1. **表情包类型**: 用户表情包、直播间表情包、充电专属表情包
2. **缓存系统**: 表情包图片本地缓存位于 `cache/images/`
3. **线程模型**: 后台工作线程处理API调用和图片加载
4. **配置管理**: 用户设置持久化存储在 `config.json`

## 使用的API端点

- 用户表情包: `https://api.bilibili.com/x/emote/user/panel/web`
- 直播间表情包: `https://api.live.bilibili.com/xlive/web-ucenter/v2/emoticon/GetEmoticons`
- 充电表情包: `https://api.bilibili.com/x/upowerv2/gw/rights/index`
- 发送弹幕: `https://api.live.bilibili.com/msg/send`

## 常见开发任务

修改此应用程序时：
1. 遵循MVC模式 - 业务逻辑放在控制器，数据处理放在模型
2. 使用线程处理网络操作以避免UI冻结
3. 维护缓存目录结构
4. 如果添加新配置选项，更新 `config.json` 处理逻辑
5. 测试快速发送和队列发送两种模式

## 构建说明

项目使用带有自定义spec文件的PyInstaller。构建包括：
- 整个 `app/` 目录
- `config.json` 文件
- 启用控制台调试的单文件可执行输出
- 可执行文件的图标文件 `main.ico`