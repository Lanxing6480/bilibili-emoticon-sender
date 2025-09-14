# app/threads.py
import traceback
import logging
from PyQt5.QtCore import QObject, pyqtSignal

class WorkerSignals(QObject):
    """
    定义正在运行的工作线程提供的信号:
    支持的信号有：
    finished: 无数据
    error: 返回一个元组： (exctype, value, traceback.format_exc())
    result: 从处理中返回的任何东西对象数据
    progress: int 类型，表示百分比进度
    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QObject):
    """
    可以运行任何函数的通用工作线程
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        """使用传入的args， kwargs初始化runner函数。"""
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            logging.error(f"Error in worker thread: {e}")
            traceback.print_exc()
            exctype, value = type(e), e
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done