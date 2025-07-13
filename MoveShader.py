import random

from OpenGL.GL import *

from ImageShader import ImageShader

class MoveShader(ImageShader):
    def __init__(self, context_id, **kwargs):
        super().__init__("yidong", context_id, **kwargs)

        self.dir_x = 0
        self.dir_y = 0

        self.reset_state()

    def set_vao(self, vertices):
        self.reset_move_vertx()

        super().set_vao(self.vertices)

    def reset_move_vertx(self):
        self.vertices = MoveShader.vertices.copy()
        # rand = random.uniform(0, 0.2) + 0.05
        # if rand < 0.15:
        #     self.dir_x = -rand
        #     self.vertices[0:2, 3] = rand
        # else:
        #     self.dir_x = rand - 0.1
        #     self.vertices[2:4, 3] = 1 - self.dir_x

        # rand = random.uniform(0, 0.25) + 0.05
        # if rand < 0.1:
        #     self.dir_y = -rand
        #     self.vertices[[1, 3], 4] = rand
        # else:
        #     self.dir_y = rand - 0.1
        #     self.vertices[[0, 2], 4] = 1 - self.dir_y


    def set_fixed_frame_count(self, num):
        super().set_fixed_frame_count(num)



    def up_tex_call_back(self):
        self.program.set_uniform(move_dir=(self.dir_x, self.dir_y))
        super().up_tex_call_back()

    def reset_state(self):
        super().reset_state()
        self.reset_move_vertx()
        self.vao.reset_vbo_data(self.vertices)

    def draw_call(self):
        glDrawArraysInstanced(GL_TRIANGLE_STRIP, 0, len(self.vertices), self.cur_draw_num)