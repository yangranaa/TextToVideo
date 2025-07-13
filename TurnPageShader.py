import random

from OpenGL.GL import *

from ImageShader import ImageShader
from VerticesTool import broken_2d_mesh, generate_triangle_strip_vertices, trans_draw_ver


class TurnPageShader(ImageShader):
    def __init__(self, context_id, **kwargs):
        vertices = generate_triangle_strip_vertices(101, 101, 0.01, 0.01)
        self.vertices = trans_draw_ver(vertices)
        super().__init__("fanye", context_id, **kwargs)

        # glEnable(GL_DEPTH_TEST)  # 启用深度测试
        # glDepthFunc(GL_LESS)


    def draw_call(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # 清除屏幕

        glDrawArraysInstanced(GL_TRIANGLE_STRIP, 0, len(self.vertices), self.cur_draw_num)