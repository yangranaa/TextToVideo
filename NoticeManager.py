from PyQt6.QtCore import QPropertyAnimation, QRect, Qt, QEasingCurve, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QLabel, QWidget, QGraphicsDropShadowEffect

from QtLayoutCss import msg_css_str

class NoticeManager(QWidget):
    _instance = None  # 类属性，用于存储单例实例

    # def set_main_window(self, widget):
    #     self.main_window = widget
    #     self.setParent(self.main_window)
    #     self.resize(self.main_window.size())

    def __init__(self, parent):
        if self._instance is not None:
            return

        super().__init__()
        self.notice_list = []
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowDoesNotAcceptFocus | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # self.setWindowOpacity(0.5)
        self.setStyleSheet(msg_css_str)
        self.resize(parent.size())

        NoticeManager._instance = self

    @classmethod
    def add_notice(cls, msg):
        cls._instance.add_msg(msg)

    def add_msg(self, msg):
        # print(msg)
        msg_item = NotificationMsg(self, msg)
        x = int(self.width() * 0.5 - msg_item.width() * 0.5)
        y = int(self.height() * 0.5)
        msg_item.setGeometry(QRect(x, y, msg_item.width(), msg_item.height()))
        msg_item.hide()
        self.notice_list.append(msg_item)
        self.update_layout()

    def update_layout(self):
        if len(self.notice_list) > 0:
            self.show()
            self.raise_()
        else:
            self.hide()

        # 更新消息布局
        for i, item in enumerate(self.notice_list):
            end_rect = QRect(item.x(), item.height() * (2 + i), item.width(), item.height())
            item.show()
            item.slide_in(end_rect)

            if not item.timer:
                def remove_item():
                    self.remove_msg(item)
                    item.close()
                    item.deleteLater()

                item.timer = QTimer(self)
                item.timer.setSingleShot(True)
                item.timer.timeout.connect(remove_item)  # 定时删除按钮
                item.timer.start(5000)  # 5 秒后触发

    def remove_msg(self, item):
        self.notice_list.remove(item)
        self.update_layout()

class NotificationMsg(QWidget):
    def __init__(self, parent, msg):
        super().__init__(parent)
        self.init_ui(msg)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.timer = None

    def init_ui(self, msg):
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        # 设置消息内容
        self.label = QLabel(msg, self)
        self.label.adjustSize()

        # 设置窗口样式
        self.setFixedSize(self.label.width() + 20, self.label.height() + 5)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

    def slide_in(self, end_rect):
        # 消息滑入动画
        self.animation.setDuration(300)  # 动画持续时间
        self.animation.setEndValue(end_rect)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBounce)  # 设置缓动曲线
        self.animation.start()
