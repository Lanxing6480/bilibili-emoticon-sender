# app/download_manager.py
import threading
import queue
import logging
import requests
import os
import json
from typing import Dict, Set, Tuple, Optional
from PyQt5.QtCore import QObject, pyqtSignal

from . import config


class DownloadTask:
    """下载任务数据类"""
    def __init__(self, local_path, url: str, emoticon_id: str, package_name: str, priority: int = 0):
        self.local_path = local_path
        self.url = url
        self.emoticon_id = emoticon_id
        self.package_name = package_name
        self.priority = priority  # 优先级：0=普通，1=高优先级（当前可见表情）

    def __eq__(self, other):
        if not isinstance(other, DownloadTask):
            return False
        return (self.url == other.url and
                self.emoticon_id == other.emoticon_id and
                self.package_name == other.package_name)

    def __hash__(self):
        return hash((self.url, self.emoticon_id, self.package_name))

    def __lt__(self, other):
        # 用于优先级队列排序，优先级高的在前
        return self.priority > other.priority


class DownloadManager(QObject):
    """
    下载管理器：使用任务队列和线程池管理图片下载
    """
    # 信号：下载完成时发出
    download_completed = pyqtSignal(str, str, str)  # url, emoticon_id, local_path
    download_failed = pyqtSignal(str, str, str)     # url, emoticon_id, error_message

    def __init__(self, model, max_workers: int = 4):
        super().__init__()
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.model = model
        self.max_workers = max_workers

        # 任务队列（使用优先级队列）
        self.task_queue = queue.PriorityQueue()

        # 线程同步
        self.lock = threading.Lock()
        self.workers = []
        self.running = True

        # 任务去重
        self.pending_tasks: Set[DownloadTask] = set()
        self.completed_tasks: Set[DownloadTask] = set()

        # 启动工作线程
        self._start_workers()

        logging.info(f"下载管理器已启动，最大工作线程数: {max_workers}")

    def _start_workers(self):
        """启动工作线程"""
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True, name=f"DownloadWorker-{i}")
            worker.start()
            self.workers.append(worker)

    def _worker_loop(self):
        """工作线程主循环"""
        while self.running:
            try:
                # 从队列获取任务（阻塞等待）
                priority, task = self.task_queue.get(timeout=1.0)

                try:
                    # 执行下载
                    local_path = self.get_emoticon_image(
                        task.local_path,
                        task.url,
                        task.emoticon_id,
                        task.package_name
                    )

                    # 发送完成信号
                    if local_path:
                        self.download_completed.emit(task.url, task.emoticon_id, local_path)
                    else:
                        self.download_failed.emit(task.url, task.emoticon_id, "下载失败")

                except Exception as e:
                    logging.error(f"下载任务执行失败 {task.url}: {e}")
                    self.download_failed.emit(task.url, task.emoticon_id, str(e))

                finally:
                    # 标记任务完成
                    with self.lock:
                        self.pending_tasks.discard(task)
                        self.completed_tasks.add(task)

                    self.task_queue.task_done()

            except queue.Empty:
                # 超时，检查是否继续运行
                continue
            except Exception as e:
                logging.error(f"工作线程异常: {e}")
                break

    def _update_mapping_file(self, mapping_file: str, emoticon_id: str, package_name: str):
        """
        更新表情包ID-名称映射文件。
        """
        try:
            mappings = {}
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)

            mappings[emoticon_id] = package_name

            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"更新映射文件失败 {mapping_file}: {e}")
    
    def get_emoticon_image(self, local_path:str, url: str, emoticon_id, package_name: str = None):
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


    def add_download_task(self,local_path: str, url: str, emoticon_id: str, package_name: str, priority: int = 0) -> bool:
        """
        添加下载任务到队列

        Args:
            url: 图片URL
            emoticon_id: 表情ID
            package_name: 表情包名称
            priority: 优先级 (0=普通, 1=高优先级)

        Returns:
            bool: 是否成功添加任务（如果任务已存在则返回False）
        """
        task = DownloadTask(local_path, url, emoticon_id, package_name, priority)

        with self.lock:
            # 检查任务是否已存在或已完成
            if task in self.pending_tasks or task in self.completed_tasks:
                logging.debug(f"下载任务已存在或已完成: {url}")
                return False

            # 添加到待处理集合
            self.pending_tasks.add(task)

        # 添加到优先级队列（优先级取负值，因为PriorityQueue是小顶堆）
        self.task_queue.put((-priority, task))

        logging.debug(f"已添加下载任务: {url}, 优先级: {priority}")
        return True

    def add_high_priority_task(self,local_path: str, url: str, emoticon_id: str, package_name: str) -> bool:
        """添加高优先级下载任务（当前可见表情）"""
        return self.add_download_task(local_path, url, emoticon_id, package_name, priority=1)

    def cancel_pending_tasks(self, emoticon_ids: Optional[Set[str]] = None):
        """
        取消待处理的任务

        Args:
            emoticon_ids: 要取消的表情ID集合，如果为None则取消所有任务
        """
        with self.lock:
            if emoticon_ids is None:
                # 取消所有任务
                self.pending_tasks.clear()
                # 清空队列
                while not self.task_queue.empty():
                    try:
                        self.task_queue.get_nowait()
                        self.task_queue.task_done()
                    except queue.Empty:
                        break
            else:
                # 取消指定表情ID的任务
                tasks_to_remove = [task for task in self.pending_tasks if task.emoticon_id in emoticon_ids]
                for task in tasks_to_remove:
                    self.pending_tasks.discard(task)

                # 从队列中移除指定任务（需要重建队列）
                temp_queue = queue.PriorityQueue()
                while not self.task_queue.empty():
                    try:
                        priority, task = self.task_queue.get_nowait()
                        if task.emoticon_id not in emoticon_ids:
                            temp_queue.put((priority, task))
                        self.task_queue.task_done()
                    except queue.Empty:
                        break

                # 将剩余任务放回原队列
                while not temp_queue.empty():
                    priority, task = temp_queue.get_nowait()
                    self.task_queue.put((priority, task))

    def get_queue_size(self) -> Tuple[int, int]:
        """获取队列状态：待处理任务数，已完成任务数"""
        with self.lock:
            return len(self.pending_tasks), len(self.completed_tasks)

    def shutdown(self):
        """关闭下载管理器"""
        self.running = False

        # 等待所有工作线程结束
        for worker in self.workers:
            worker.join(timeout=5.0)

        logging.info("下载管理器已关闭")

    def __del__(self):
        """析构函数，确保资源清理"""
        self.shutdown()