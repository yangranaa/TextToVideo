
from OpenGL.GL import *

from ImageShader import ImageShader
from MyLog import MyLog


class NormalShader(ImageShader):
    def __init__(self, shader_name, context_id, **kwargs):
        super().__init__(shader_name, context_id, **kwargs)

    def draw_call(self):
        glDrawArraysInstanced(GL_TRIANGLE_STRIP, 0, len(self.vertices), self.cur_draw_num)