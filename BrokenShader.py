import random

import numpy as np
from PyQt6 import QtGui

from GlProgram import GlVao, GlVbo, GlTextureArray, GlTexture, GlPboGroup
from GlobalData import GlobalData
from ImageShader import ImageShader
from OpenGL.GL import *

from NormalShader import NormalShader
from Setting import Setting
from VerticesTool import fill_point, broken_2d_mesh, set_group_rot_point


class BrokenShader(ImageShader):
    vertices = np.array([
        [-1.0, -1.0, 0.0, 0.0, 0.0],
        [1.0, -1.0, 0.0, 1.0, 0.0],
        [1.0, 1.0, 0.0, 1.0, 1.0],
        [-1.0, 1.0, 0.0, 0.0, 1.0],

    ], dtype=np.float32)

    # vertices = fill_point(vertices, 11)
    # vertices = broken_2d_mesh(vertices, 10)
    # vertices[:, 8:] = [0, 0, -1]

    def __init__(self, context_id, **kwargs):
        self.reset_vertices()

        super().__init__('suiping', context_id, **kwargs)

        self.read_pix_pbos = None


        self.projection = QtGui.QMatrix4x4()
        self.projection.ortho(-1, 1, -1, 1, -5, 5)
        self.program.set_uniform(projectionMatrix=self.projection)

        # glEnable(GL_DEPTH_TEST)  # 启用深度测试
        # glDepthFunc(GL_LESS)

        # random_video = random.choice(GlobalData().video_paths)
        # self.bg_shader = NormalShader('wuxiaoguo', context_id, video_path=random_video, parallel_render=True, loop=True)

    def set_output(self, out_width, out_height):
        self.out_width, self.out_height = out_width, out_height
        self.out_img_size = self.out_width * self.out_height * 3

        self.read_pix_pbos = GlPboGroup(self.context_id, 2, GL_PIXEL_PACK_BUFFER, GL_STREAM_READ)
        self.read_pix_pbos.resize_pbos(self.out_img_size)


    def read_shader_result(self, read_size):
        if self.read_pix_pbos:
            cur_pbo = self.read_pix_pbos.get_cur_pbo()
            if read_size > 0:
                cur_pbo.down_data_from_render_buff(self.out_width, self.out_height, GL_RGB)
                cur_pbo.down_size = self.out_img_size

            next_pbo = self.read_pix_pbos.get_next_pbo()
            if next_pbo.down_size > 0:
                data = next_pbo.map_data_to_cpu()
                next_pbo.down_size = 0
            else:
                data = None

            self.read_pix_pbos.step_pbo_id()

            return data
        else:
            return None

    def get_max_draw(self):
        self.max_draw_ins = 1

        return self.max_draw_ins

    def reset_vertices(self):
        self.vertices = fill_point(BrokenShader.vertices, 11)
        self.vertices = broken_2d_mesh(self.vertices, 10)
        set_group_rot_point(self.vertices)
        self.vertices[:, 8:] = [0, 0, -1]

    def set_vao(self, vertices):
        self.vao = GlVao(self.context_id, self.vertices, fmt=(3, 2, 3, 3))
        self.vertices = vertices

    def draw_call(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # 清除屏幕

        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices))

        if self.time_count >= 6:
            self.time_count = 0.0
            self.reset_vertices()
            self.set_vao(self.vertices)

    # def shader_img(self):
        # self.bg_shader.shader_img()
        #
        # result = super().shader_img()
        #
        # if result:
        #

