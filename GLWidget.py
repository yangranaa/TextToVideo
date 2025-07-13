import math

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QSurfaceFormat
from OpenGL.GL import *
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

from GlobalData import GlobalData
from ShaderQueue import ShaderQueue, ShaderManager

class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resolution = None
        self.fixed_view_w = None
        self.fixed_view_h = None

        # 设置 OpenGL 版本
        q_format = QSurfaceFormat()
        q_format.setVersion(4, 5)
        q_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        # format.setDepthBufferSize(24)
        self.setFormat(q_format)
        # q_format.setDefaultFormat(q_format)

        self.fixed_img = None
        self.clear_shader = False

        self.shader_queue = None
        self.view_fbo = None
        self.need_refresh = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(33)

    def initializeGL(self):
        """初始化 OpenGL 环境"""
        super().initializeGL()
        # glEnable(GL_DEPTH_TEST)  # 启用深度测试
        # glDepthFunc(GL_LESS)

    def set_fixed_shader(self, img_path, eff, enter_eff, after_eff):
        self.fixed_img = img_path
        self.fixed_eff = eff
        self.enter_eff = enter_eff
        self.after_eff = after_eff

    def refresh_gl(self):
        if not GlobalData().video_paths:
            return

        self.need_refresh = True

    def random_shader_queue(self):
        self.clear_shader_queue()

        random_video = GlobalData().get_random_video()
        eff = GlobalData().get_random_active_eff()

        if random_video:
            args = {'eff':eff, 'video_path':random_video}
            self.shader_queue = ShaderManager.create_shader_queue(0, **args)

    def paintGL(self):
        """绘制 OpenGL 场景"""
        if self.view_fbo is None:
            self.view_fbo = self.defaultFramebufferObject()

        if self.fixed_img is not None:
            self.clear_shader_queue()

            self.shader_queue = ShaderManager.create_shader_queue(0,
                                                                  view_fbo=self.view_fbo,
                                                                  eff=self.fixed_eff,
                                                                  enter_eff=self.enter_eff,
                                                                  resolution=self.resolution)
            self.shader_queue.set_fixed_img(self.fixed_img)
            if self.after_eff:
                self.shader_queue.add_after_eff(self.after_eff)

            self.fixed_img = None

        if self.need_refresh:
            self.random_shader_queue()
            self.need_refresh = False

        if self.clear_shader:
            self.clear_shader = False
            self.clear_shader_queue()

        if self.shader_queue:
            self.shader_queue.shader_queue()
        else:
            glClearColor(0, 0, 0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)


    def clear_shader_queue(self):
        if self.shader_queue:
            self.shader_queue.clear_queue()
            self.shader_queue = None

    def resizeGL(self, width, height):
        """处理窗口大小变化"""
        self.reset_view()

    def set_fixed_view_port(self, w, h):
        self.fixed_view_w = w
        self.fixed_view_h = h

        self.setFixedSize(w, h)
        self.resolution = (w, h)

    def reset_view(self):
        pass

        # shader = self.shader_queue.get_active_shader()
        #
        # if shader is None:
        #     return
        #
        # if self.fixed_view_w:
        #     w, h = self.fixed_view_w, self.fixed_view_h
        #     glViewport(0, 0, w, h)
        # else:
        #
        #     resolution = GlobalData().video_resolution
        #     if resolution is None:
        #         if shader.width <= 0:
        #             return
        #         resolution = shader.width / shader.height
        #
        #     width, height = self.width(), self.height()
        #     w, h = width, height
        #     if width / height > resolution:
        #         w = math.floor(h * resolution)
        #     else:
        #         h = math.floor(w / resolution)
        #
        #     off_set_x = math.floor((width - w) * 0.5)
        #     off_set_y = math.floor((height - h) * 0.5)
        #     glViewport(off_set_x, off_set_y, w, h)  # 设置视口大小
        #
        #     self.resolution = (w, h)
        #
        #     self.shader_queue.set_resolution(*self.resolution)

        # print(width, height, resolution, off_set_x, off_set_y)
