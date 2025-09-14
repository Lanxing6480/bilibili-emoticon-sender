# app package initialization
# Bilibili Emoticon Sender Application Modules

__version__ = "2.1.0"
__author__ = "Your Name"
__description__ = "Bilibili Live Emoticon Sender Application"

# Import key components for easier access
from .models import EmoticonManager
from .views import MainWindow
from .controllers import MainController
from .threads import Worker, WorkerSignals

__all__ = [
    'EmoticonManager',
    'MainWindow',
    'MainController',
    'Worker',
    'WorkerSignals'
]