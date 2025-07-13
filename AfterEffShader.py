from GlProgram import GlProgram, GlVao, GlFbo, GlTextureArray
from VerticesTool import screen_vertices
from OpenGL.GL import *


class AfterEffShader:

    vertices = screen_vertices

    def __init__(self, context_id, view_fbo, resolution, eff_name_list=None):
        self.output_texs = None
        self.out_height = None
        self.out_width = None
        self.tex_num = None
        self.context_id = context_id
        self.view_fbo = view_fbo
        self.resolution = resolution
        self.target_shader = None

        self.time_count = 0.0
        self.time_step = 0.033

        self.eff_list = []
        self.add_eff(eff_name_list)

        self.vao = None
        self.fbo = None

        if self.view_fbo:
            self.fbo = GlFbo(self.context_id, *self.resolution)

            self.set_uniform(resolution=self.resolution)
        else:
            self.set_uniform(off_screen=1)


    def add_eff(self, eff_name_list):
        for eff_name in eff_name_list:
            program = GlProgram.get_program(eff_name, self.context_id)
            program.location_tex('renderedTexture', GL_TEXTURE1, 1)
            self.eff_list.append(program)

    def set_uniform(self, **kwargs):
        for eff_program in self.eff_list:
            eff_program.set_uniform(**kwargs)

    def set_output_texs(self, ouput_tex):
        if self.output_texs is None:
            self.out_width, self.out_height = ouput_tex.width, ouput_tex.height
            self.tex_num = ouput_tex.tex_num

            self.output_texs = GlTextureArray(self.context_id, self.out_width, self.out_height, self.tex_num,
                                              c_fmt=GL_RGBA8, is_down_tex=True)

            self.output_texs.bind_img_texture(1)
        else:
            self.output_texs.bind_img_texture(1)


    def draw_call(self, target_shader):

        if self.fbo:

            glBindFramebuffer(GL_FRAMEBUFFER, self.fbo.fbo_id)
            glViewport(0, 0, *self.resolution)
            glClearColor(0, 0, 0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

        target_shader.draw_call()

        glMemoryBarrier(GL_ALL_BARRIER_BITS)

        # 绘制完再创建vao 避免影响原始状态
        if self.vao is None:
            self.vao = GlVao(self.context_id, self.vertices)

        for eff_program in self.eff_list:
            eff_program.set_uniform(time=self.time_count)

            glBindVertexArray(self.vao.vao_id)

            if self.view_fbo:
                glActiveTexture(GL_TEXTURE1)
                glBindTexture(GL_TEXTURE_2D, self.fbo.tex.texture_id)

                if eff_program == self.eff_list[-1]:
                    glBindFramebuffer(GL_FRAMEBUFFER, self.view_fbo)
            else:
                self.set_output_texs(target_shader.output_texs)

            glDrawArraysInstanced(GL_TRIANGLE_STRIP, 0, len(self.vertices), target_shader.cur_draw_num)

        if self.output_texs:
            target_shader.set_ae_output_texs(self.output_texs)

        self.time_count += self.time_step * target_shader.cur_draw_num


    def release(self):

        if self.vao:
            self.vao.release()
            self.vao = None

        if self.fbo:
            self.fbo.release()
            self.fbo = None

        if self.output_texs:
            self.output_texs.release()
            self.output_texs = None