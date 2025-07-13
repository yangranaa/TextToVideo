
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout

from QtLayoutCss import qrcode_css_str


class QrcodeNotice(QWidget):

    def __init__(self, parent, img_path):
        super().__init__(parent)
        self.setWindowTitle("微信扫码登录")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet(qrcode_css_str)
        self.move(parent.pos())

        self.lay = QHBoxLayout()
        self.setLayout(self.lay)

        self.qr_img = QLabel()
        pixmap = QPixmap(img_path)
        self.qr_img.setPixmap(pixmap)
        self.lay.addWidget(self.qr_img)

        self.label = QLabel("这二维码不是作者所有，本软件的配音功能是使用人家的试用功能一片片连接起来的。这家语音试用也需要登录，扫码授权登录即可，不用充钱。 有更好的配音也可以推荐给作者。")
        self.label.setWordWrap(True)
        self.label.setFixedHeight(435)
        self.lay.addWidget(self.label)

        self.show()

    def change_img(self, img_path):
        pixmap = QPixmap(img_path)
        self.qr_img.setPixmap(pixmap)

    def set_close_cb(self, cb_fun):
        self.cb_fun = cb_fun

    def closeEvent(self, event):
        if self.cb_fun:
            self.cb_fun()