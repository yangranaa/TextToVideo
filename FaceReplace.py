import numpy as np

from GlProgram import GlTexture, GlVao, GlVbo
from GlobalData import GlobalData
from ImageShader import ImageShader
from OpenGL.GL import *

import mediapipe as mp

face_mesh = mp.solutions.face_mesh

class FaceReplace(ImageShader):

    def __init__(self, context_id, **kwargs):
        super().__init__('face_replace', context_id, **kwargs)

        self.rfm = GlobalData().replace_face_manage

        img = self.rfm.src_img

        self.face_texture = GlTexture(self.context_id, 0, use_unit=GL_TEXTURE1)
        self.program.location_tex('face', GL_TEXTURE1, 1)
        self.face_texture.resize_tex(img.shape[1], img.shape[0])
        self.face_texture.up_tex_immediately(img)

        self.set_vao(self.rfm.vertices)

    def get_max_draw(self):
        if self.context_id:
            self.max_draw_ins = 8
        else:
            self.max_draw_ins = 1

        return self.max_draw_ins

    def up_tex_call_back(self):
        state = self.gl_state_cache.popleft()

        glUseProgram(self.program.program)

        self.cur_draw_num = state.get('draw_num')
        self.vao.reset_vbo_data(state.get('comb_vertices'))
        glMultiDrawArrays(GL_TRIANGLES, state.get('first_list'), state.get('count_list'), self.cur_draw_num)

    def cache_gl_state(self, imgs):
        draw_num = len(imgs)
        if draw_num <= 0:
            return

        off_set = 0
        first_list = []
        count_list = []
        vertices_list = []
        for img in imgs:
            vertices = self.rfm.get_face_map_vertx(img)
            first_list.append(off_set)
            off_set += len(vertices)
            count_list.append(len(vertices))
            vertices_list.append(vertices)

        first_list = np.array(first_list, dtype=np.int32)
        count_list = np.array(count_list, dtype=np.int32)

        comb_vertices = np.empty((off_set, 5), dtype=np.float32)
        off_set = 0
        idx = 0
        for vertices in vertices_list:
            vertices[:, 2] = idx
            comb_vertices[off_set: off_set + len(vertices)] = vertices
            off_set += len(vertices)
            idx += 1

        args = {"first_list": first_list, "count_list": count_list,"comb_vertices":comb_vertices,"draw_num":draw_num}

        self.gl_state_cache.append(args)

    def set_vao(self, vertices):
        self.vao = GlVao(self.context_id, vertices, fmt=(3, 2), usage=GL_STREAM_DRAW)
        self.vertices = vertices




