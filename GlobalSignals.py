from PyQt6.QtCore import QObject, pyqtSignal


class GlobalSignals(QObject):
    reset_shot_data = pyqtSignal()

# 创建全局实例
global_signals = GlobalSignals()