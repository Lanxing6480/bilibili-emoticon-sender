## 自动循环发送功能没实现
## 图片加载优化 
## 请求优化，减少非必要请求
## 增加缓存机制，本地保存表情包缩略图
## 模块化，方便维护
~~ 添加自定义表情保存和发送（提供表情ID）~~
~~ 手动添加充电表情（提供充电的UP的UID），注意该UID不能自动化获取，所以表情需要持久化保存 ~~ (已解决)(只需要获取当前直播间的UP充电表情即可)
## 对颜文字表情的支持
-- 报错:
    OpenType support missing for "SimSun", script 18
    OpenType support missing for "Arial", script 18
    OpenType support missing for "MS UI Gothic", script 18
## 对热词系列的支持
-- 报错:
    libpng warning: iCCP: known incorrect sRGB profile
    libpng warning: iCCP: known incorrect sRGB profile
    libpng warning: iCCP: known incorrect sRGB profile
    libpng warning: iCCP: known incorrect sRGB profile
    ......

## 添加运行日志(使用**logging**)
## 优化逻辑,实现异步机制

## 缓存系统优化 (2025-10-04)
- 修复表情包ID相同但名称改变时的缓存刷新问题
- 实现按表情包名称分类的缓存目录结构
- 添加表情包ID-名称映射文件机制
- 实现特殊表情包重命名规则：
  - UP主大表情 → {UP主名称}大表情
  - 房间专属表情 → {UP主名称}房间专属表情
  - 为TA充电 → {UP主名称}充电表情
- 保持向后兼容性，支持新旧缓存系统共存


## 图片下载系统优化 (2025-10-04)
- 修复切换页面过快导致创建巨量下载进程卡死的问题
- 新增下载管理模块download_manager.py, 使用队列+多线程进行下载
- 修复表情包ID-名称映射文件写入竞态问题, 使用队列保存任务, 定时合并写入
## 代办
## 房间号-UID-名称缓存系统 (2025-10-09)
- 实现房间号-UID-名称本地缓存机制，减少重复API请求
- 缓存文件存储在 `cache/room_cache.json`，格式：{room_id: {"uid": uid, "name": name}}
- 房间号和UID为强绑定关系，名称支持后续刷新
- 修改 `get_UP_UID` 和 `_get_up_name_from_room` 方法优先使用缓存
- 新增 `_get_up_name_from_api` 方法用于通过UID获取名称

## GUI直播间ID下拉选择功能 (2025-10-09)
- 将房间号输入框改为可编辑的下拉选择框 (QComboBox)
- 下拉框显示格式："主播名称 (房间号)"
- 支持手动输入和选择历史房间
- 自动从缓存加载历史房间信息
- 每次加载表情包后自动更新下拉框内容
- 配置保存和加载支持新的下拉框格式

## 代办
保存的"大表情""房间表情""充电表情"等名字上的错误
手动强制刷新的按钮
直播间快捷切换 (已实现)