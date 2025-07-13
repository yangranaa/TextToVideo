
import sys

import traceback

from OpenGL.GL import *
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QMainWindow, QApplication

from GlobalData import GlobalData


from ShaderQueue import ShaderManager
from ShotData import ShotData
from VideoWrite import VideoWrite


class OpenGLWidget(QOpenGLWidget):
    finished = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view_fbo = None
        self.shader = None
        self.shader_que = None

        # 设置 OpenGL 版本
        format = QSurfaceFormat()
        format.setVersion(5, 4)
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        self.setFormat(format)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(33)

        GlobalData().load_op_cache()
        GlobalData().read_srt_data()
        ShotData.read_data_from_file()

        # vw = VideoWrite(self)
        # vw.start_write_thread()


    def initializeGL(self):
        super().initializeGL()

        # 初始化 OpenGL 上下文
        glClearColor(0, 0, 0, 1.0)  # 设置背景颜色
        # glEnable(GL_DEPTH_TEST)  # 启用深度测试
        # glDepthFunc(GL_LESS)


    def init_shader_que(self):
        img = r"C:\Users\Administrator\Desktop\ttest\图片\1733075738208.jpg"

        self.view_fbo = self.defaultFramebufferObject()
        self.shader_que = ShaderManager.create_shader_queue(0,
                                                            view_fbo=self.view_fbo,
                                                            eff="tupian",
                                                            enter_eff="xiexian",
                                                            resolution=(1024, 768))
        self.shader_que.set_fixed_img(img)
        self.shader_que.add_after_eff("jinfen")
        # self.shader_que = None

    def paintGL(self):
        # 清除缓冲区

        if self.shader:
            self.shader.shader_img()

        if self.shader_que:
            self.shader_que.shader_queue()
        else:
            self.init_shader_que()


    def resizeGL(self, width, height):
        # 视口调整
        glViewport(0, 0, width, height)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt5 OpenGL Demo")
        w, h = 1024, 768

        self.setGeometry(100, 100, w, h)

        # 创建 OpenGL 部件
        self.glWidget = OpenGLWidget(self)
        self.setCentralWidget(self.glWidget)
        self.setFixedSize(w, h)

def exception_hook(exctype, value, tb):
    print(f"Unhandled exception: {exctype.__name__}: {value}")
    print("Traceback (most recent call last):")
    traceback.print_tb(tb)  # 打印调用堆栈

if __name__ == "__main__":
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

