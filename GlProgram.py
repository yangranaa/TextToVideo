import random
import sys

import numpy as np
from OpenGL.GL import *

from OpenGL.GL.shaders import compileProgram, compileShader
from PyQt6.QtGui import QMatrix4x4, QOpenGLContext, QOffscreenSurface

from Setting import Setting


class GlContext:
    _contexts = {}

    @classmethod
    def get_context(cls, context_id):

        if cls._contexts.get(context_id) is None:
            cls._contexts[context_id] = GlContext(context_id)

        Setting.set("max_draw_ins", min(glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS), Setting.get('max_draw_ins')))

        return cls._contexts[context_id]

    @classmethod
    def release_context(cls, context_id):
        context = cls._contexts.get(context_id)
        if context is not None:
            context.release()

        cls._contexts[context_id] = None

    def __init__(self, context_id):
        self.context_id = context_id
        # 主线程context_id = 0
        if context_id == 100:
            self.gl_context = QOpenGLContext()
            self.gl_context.create()
            self.surface = QOffscreenSurface()
            self.surface.create()
            self.gl_context.makeCurrent(self.surface)


        self.fbo = []
        self.tex = []
        self.pbo = []
        self.vao = []
        self.vbo = []

    def release(self):
        GlProgram.release_context(self.context_id)

        glDeleteVertexArrays(len(self.vao), self.vao)
        glDeleteBuffers(len(self.vbo), self.vbo)
        glDeleteFramebuffers(len(self.fbo), self.fbo)
        glDeleteTextures(len(self.tex), self.tex)
        glDeleteBuffers(len(self.pbo), self.pbo)

        # self.surface.deleteLater()
        # self.gl_context.deleteLater()

        self._contexts[self.context_id] = None


class GlProgram:
    import shader_code
    code_module = sys.modules['shader_code']

    _program_dict = {}

    @classmethod
    def get_program(cls, shader_name, context_id):
        if cls._program_dict.get(context_id) is None:
            cls._program_dict[context_id] = {}

        if cls._program_dict[context_id].get(shader_name) is None:
            cls._program_dict[context_id][shader_name] = GlProgram(context_id, shader_name)

        return cls._program_dict[context_id][shader_name]

    @classmethod
    def release_context(cls, context_id):
        for prog in cls._program_dict[context_id].values():
            prog.release()

        cls._program_dict[context_id] = {}

    def __init__(self, context_id, shader_name):
        self.context_id = context_id

        vex_code = getattr(self.code_module, f'{shader_name}_vertex')
        frag_code = getattr(self.code_module, f'{shader_name}_fragment')

        vertex_shader = compileShader(vex_code, GL_VERTEX_SHADER)
        fragment_shader = compileShader(frag_code, GL_FRAGMENT_SHADER)


        self.program = compileProgram(vertex_shader, fragment_shader)

    def use_program(self):
        glUseProgram(self.program)

    def location_tex(self, sampler_name, channel, chan_id):
        glUseProgram(self.program)
        glActiveTexture(channel)

        texture_sampler_location = glGetUniformLocation(self.program, sampler_name)
        glUniform1i(texture_sampler_location, chan_id)  # 0 表示 GL_TEXTURE0
        glActiveTexture(GL_TEXTURE0)

    def set_uniform(self, **kwargs):
        glUseProgram(self.program)
        for k, v in kwargs.items():
            u_location = glGetUniformLocation(self.program, k)
            if u_location == -1:
                #  my_log.info(f'着色器不存在变量{k}')
                continue
            if isinstance(v, float):
                glUniform1f(u_location, v)
            elif isinstance(v, int):
                glUniform1i(u_location, v)
            elif isinstance(v, tuple) and len(v) == 2:
                if type(v[0]) is float:
                    glUniform2f(u_location, *v)
                else:
                    glUniform2i(u_location, *v)
            elif isinstance(v, QMatrix4x4):
                glUniformMatrix4fv(u_location, 1, GL_FALSE, v.data())

    def release(self):
        glDeleteProgram(self.program)


class GlFbo:

    def __init__(self, context_id, width, height):
        self.context_id = context_id
        self.width = width
        self.height = height

        self.tex = GlTexture(self.context_id, 0)
        self.tex.resize_tex(self.width, self.height)

        self.fbo_id = glGenFramebuffers(1)

        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_id)
        glBindTexture(GL_TEXTURE_2D, self.tex.texture_id)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.tex.texture_id, 0)

        # self.depth_rbo = glGenRenderbuffers(1)
        # glBindRenderbuffer(GL_RENDERBUFFER, self.depth_rbo)
        # glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
        # glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT,
        #                           GL_RENDERBUFFER, self.depth_rbo)

        GlContext.get_context(context_id).fbo.append(self.fbo_id)


    def release(self):
        glDeleteFramebuffers(1, [self.fbo_id])
        self.tex.release()


class GlPbo:

    def __init__(self, context_id):
        self.upload_cb = None
        self.img_num = 0
        self.down_size = 0
        self.context_id = context_id
        self.pbo_id = glGenBuffers(1)
        self.width = 0
        self.height = 0
        self.chan_num = 3

        GlContext.get_context(self.context_id).pbo.append(self.pbo_id)

    def map_data_to_pbo(self, data):
        glBindBuffer(self.target, self.pbo_id)
        # glBufferData(self.target, data.nbytes, None, self.usage)
        glBufferSubData(self.target, 0, data.nbytes, None)

        ptr = glMapBufferRange(self.target, 0, data.nbytes,
                               GL_MAP_WRITE_BIT | GL_MAP_UNSYNCHRONIZED_BIT)

        ctypes.memmove(ptr, data.ctypes.data, data.nbytes)
        glUnmapBuffer(self.target)

        del data

    def upload_date_to_texture(self, texture_id, width, height, fmt):
        # start_time = time.time()
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glBindBuffer(self.target, self.pbo_id)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, fmt, GL_UNSIGNED_BYTE, None)
        # end_time = time.time()
        # MyLog.info("上传单纹理用时:", end_time-start_time)


    def upload_date_to_texture_arr(self, texture_id, width, heigth, layers, fmt):
        # start_time = time.time()

        glBindTexture(GL_TEXTURE_2D_ARRAY, texture_id)
        glBindBuffer(self.target, self.pbo_id)
        glTexSubImage3D(GL_TEXTURE_2D_ARRAY, 0, 0, 0, 0, width, heigth, layers, fmt,
                        GL_UNSIGNED_BYTE, None)

        # end_time = time.time()
        # MyLog.info("上传纹理数组用时:", end_time - start_time)

    def down_data_from_render_buff(self, width, height, c_fmt):
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindBuffer(self.target, self.pbo_id)
        glReadPixels(0, 0, width, height, c_fmt, GL_UNSIGNED_BYTE, 0)

    def map_data_to_cpu(self):
        glBindBuffer(self.target, self.pbo_id)
        ptr = glMapBuffer(self.target, GL_READ_ONLY)

        data = np.frombuffer((ctypes.c_ubyte * self.down_size).from_address(ptr),
                             dtype=np.uint8)
        data = np.copy(data)

        glUnmapBuffer(self.target)
        # glBindBuffer(self.target, 0)

        return data

    def down_data_from_tex_img(self, texture_id, fmt):
        glBindBuffer(self.target, self.pbo_id)
        glBindTexture(GL_TEXTURE_2D_ARRAY, texture_id)
        # glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)
        glGetTexImage(GL_TEXTURE_2D_ARRAY, 0, fmt, GL_UNSIGNED_BYTE, 0)

    # def set_data_save_ssbo(self):
    #     glBindBufferBase(self.target, 0, self.pbo_id)
    #
    # def read_data_from_ssbo(self, size):
    #     glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
    #     glBindBufferBase(self.target, 0, self.pbo_id)
    #     ptr = glMapBuffer(self.target, GL_READ_ONLY)
    #
    #     data = np.frombuffer((ctypes.c_ubyte * size).from_address(ptr),
    #                          dtype=np.uint8)
    #     data = np.copy(data)
    #     glUnmapBuffer(self.target)
    #     return data

    def resize(self, size, target, usage):
        self.target = target
        self.usage = usage
        self.size = size

        glFlush()
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindBuffer(target, self.pbo_id)
        glBufferData(target, self.size, None, usage)

        if target == GL_SHADER_STORAGE_BUFFER:
            glBindBufferBase(target, 0, self.pbo_id)

    def release(self):
        glDeleteBuffers(1, [self.pbo_id])

class GlPboGroup:

    # type
    # GL_STATIC_DRAW 极少修改
    # GL_STREAM_DRAW 每帧写
    # GL_STREAM_READ 每帧写

    def __init__(self, context_id, pbo_num, target, usage):
        self.context_id = context_id
        self.pbos = [GlPbo(context_id) for _ in range(pbo_num)]
        self.cur_pbo = 0
        self.pbo_num = pbo_num
        self.step_num = 1
        self.target = target
        self.usage = usage

    def get_cur_pbo(self):
        return self.pbos[self.cur_pbo]

    def get_next_pbo(self):
        idx = self.cur_pbo - self.step_num
        if idx == -1:
            idx += self.pbo_num
        if idx == self.pbo_num:
            idx = 0

        return self.pbos[idx]

    def resize_pbos(self, size):
        for pbo in self.pbos:
            pbo.resize(size, self.target, self.usage)

    #
    # def set_save_ssbo(self):
    #     cur_ssbo = self.get_cur_pbo()
    #     cur_ssbo.set_data_save_ssbo()
    #
    # def read_data_from_ssbo(self, size):
    #     next_ssbo = self.get_next_pbo()
    #     data = next_ssbo.read_data_from_ssbo(size)
    #     self.step_pbo_id()
    #
    #     return data

    def step_pbo_id(self):
        self.cur_pbo += self.step_num
        if self.cur_pbo == -1:
            self.cur_pbo += self.pbo_num
        elif self.cur_pbo == self.pbo_num:
            self.cur_pbo = 0

    def release(self):
        for pbo in self.pbos:
            pbo.release()

class GlTexture:

    def __init__(self, context_id, use_pbo_num=2, c_fmt=GL_RGB, use_unit=GL_TEXTURE0):
        self.context_id = context_id
        self.texture_id = glGenTextures(1)
        self.use_pbo_num = use_pbo_num
        self.pbo_group = None
        self.c_fmt = c_fmt
        self.use_unit = use_unit

        if c_fmt == GL_RGB:
            self.c_channal_num = 3

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)

        GlContext.get_context(self.context_id).tex.append(self.texture_id)

        if use_pbo_num > 0:
            self.pbo_group = GlPboGroup(context_id, use_pbo_num, GL_PIXEL_UNPACK_BUFFER, GL_STREAM_DRAW)

    def resize_tex(self, width, height):
        self.width = width
        self.height = height
        self.size = width * height * self.c_channal_num


        glFlush()
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)  # 解绑所有PBO
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, self.c_fmt, width, height, 0, self.c_fmt, GL_UNSIGNED_BYTE, None)

        if self.pbo_group:
            self.pbo_group.resize_pbos(self.size)


    def up_tex_to_gl(self, img, first_skip=False):
        glActiveTexture(self.use_unit)

        cur_pbo = self.pbo_group.get_cur_pbo()
        cur_pbo.map_data_to_pbo(img)

        if not first_skip:
            next_pbo = self.pbo_group.get_next_pbo()
            next_pbo.upload_date_to_texture(self.texture_id, self.width, self.height, self.c_fmt)

        self.pbo_group.step_pbo_id()


    def up_tex_immediately(self, img):
        # 同步
        glActiveTexture(self.use_unit)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, self.c_fmt, self.width, self.height, 0, self.c_fmt, GL_UNSIGNED_BYTE, img)
        glActiveTexture(GL_TEXTURE0)

    def release(self):
        glDeleteTextures(1, [self.texture_id])

        if self.pbo_group:
            self.pbo_group.release()

class GlTextureArray:

    def __init__(self, context_id, width, height, tex_num, use_unit=GL_TEXTURE0, use_pbo_num=2, c_fmt=GL_RGB8, is_down_tex=False):
        self.context_id = context_id
        self.tex_arr_id = glGenTextures(1)
        self.use_pbo_num = use_pbo_num
        self.pbo_group = None
        self.tex_num = tex_num
        self.width = width
        self.height = height
        self.use_unit = use_unit
        self.pingpong_start = True

        self.trans_fmt = GL_RGB

        self.c_fmt = c_fmt
        if c_fmt == GL_RGB8:
            self.c_channal_num = 3
        elif c_fmt == GL_RGBA8:
            self.c_channal_num = 3

        self.read_size = self.width * self.height * self.tex_num * self.c_channal_num  # 上传 下载都只用3色 A通道只是上传格式需求 传输后舍弃

        if is_down_tex:
            self.p_target = GL_PIXEL_PACK_BUFFER
            self.p_useage = GL_STREAM_READ
        else:
            self.p_target = GL_PIXEL_UNPACK_BUFFER
            self.p_useage = GL_STREAM_DRAW

        glFlush()
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)  # 解绑所有PBO

        glBindTexture(GL_TEXTURE_2D_ARRAY, self.tex_arr_id)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        # glTexStorage3D 初始化后即不可更改
        glTexStorage3D(GL_TEXTURE_2D_ARRAY, 1, self.c_fmt, self.width, self.height, self.tex_num)

        GlContext.get_context(self.context_id).tex.append(self.tex_arr_id)

        if use_pbo_num > 0:
            self.pbo_group = GlPboGroup(context_id, use_pbo_num, self.p_target, self.p_useage)
            self.pbo_group.resize_pbos(self.read_size)


    def bind_tex(self):
        glActiveTexture(self.use_unit)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.tex_arr_id)

    def bind_img_texture(self, tex_unit=0):
        glBindImageTexture(tex_unit, self.tex_arr_id, 0, GL_TRUE, 0, GL_READ_WRITE, GL_RGBA8UI)

    def clear_tex_color(self):
        glClearTexImage(self.tex_arr_id, 0, GL_RGB, GL_UNSIGNED_BYTE, np.array([255,0,0],dtype=np.uint8))

    def up_tex_arr_to_gl(self, imgs, upload_cb=None):
        glActiveTexture(self.use_unit)

        img_num = len(imgs)

        cur_pbo = self.pbo_group.get_cur_pbo()

        if img_num > 0:
            cur_pbo.map_data_to_pbo(imgs)
            cur_pbo.upload_cb = upload_cb
            cur_pbo.img_num = img_num

        next_pbo = self.pbo_group.get_next_pbo()
        if next_pbo.upload_cb is not None:
            next_pbo.upload_date_to_texture_arr(self.tex_arr_id, self.width, self.height, next_pbo.img_num, self.trans_fmt)
            next_pbo.upload_cb()
            next_pbo.upload_cb = None
            next_pbo.img_num = 0

        self.pbo_group.step_pbo_id()

    def up_tex_immediately(self, img):
        # 同步
        glActiveTexture(self.use_unit)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.tex_arr_id)
        glTexSubImage3D(GL_TEXTURE_2D_ARRAY, 0, 0, 0, 0, self.width, self.height, 1, self.trans_fmt,
                        GL_UNSIGNED_BYTE, img)

        glActiveTexture(GL_TEXTURE0)

    def down_tex_to_cpu(self, down_size):

        cur_pbo = self.pbo_group.get_cur_pbo()
        if down_size > 0:
            cur_pbo.down_data_from_tex_img(self.tex_arr_id, self.trans_fmt)
            cur_pbo.down_size = down_size

        next_pbo = self.pbo_group.get_next_pbo()
        if next_pbo.down_size > 0:
            data = next_pbo.map_data_to_cpu()
            next_pbo.down_size = 0
        else:
            data = None


        self.pbo_group.step_pbo_id()

        return data



    def release(self):
        glDeleteTextures(1, [self.tex_arr_id])

        if self.pbo_group:
            self.pbo_group.release()

class GlVbo:

    _vbos = {}

    # @classmethod
    # def get_vbo(cls, context_id, vertices, usage=GL_STATIC_DRAW):
    #     if cls._vbos.get(context_id) is None:
    #         cls._vbos[context_id] = {}
    #
    #     key = id(vertices)
    #     if cls._vbos[context_id].get(key) is None:
    #         cls._vbos[context_id][key] = GlVbo(context_id, vertices, usage)
    #
    #     return cls._vbos[context_id][key]
    #
    # @classmethod
    # def release_context(cls, context_id):
    #     vbo_list = [vbo.vbo_id for vbo in cls._vbos[context_id].values()]
    #     glDeleteBuffers(len(vbo_list), vbo_list)
    #     cls._vbos[context_id] = {}
    #
    # @classmethod
    # def release_vbo(cls, context_id, vertices):
    #     key = id(vertices)
    #     vbo = cls._vbos[context_id][key]
    #     glDeleteBuffers(1, [vbo.vbo_id])
    #     cls._vbos[context_id][key] = None

    def __init__(self, context_id, vertices, usage):
        self.vbo_id = glGenBuffers(1)
        self.usage = usage
        self.context_id = context_id
        self.size = vertices.nbytes
        self.vertices = vertices

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, self.usage)

        GlContext.get_context(context_id).vbo.append(self.vbo_id)

    def reset_data(self, vertices):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
        if self.size == vertices.nbytes:
            glBufferSubData(GL_ARRAY_BUFFER, 0, vertices.nbytes, vertices)
        else:
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, self.usage)
            self.size = vertices.nbytes

    def release(self):
        glDeleteBuffers(1, [self.vbo_id])


class GlVao:
    _vaos = {}

    # @classmethod
    # def get_vao(cls, context_id, vertices, fmt=(3,2), ins_data, ins_fmt):
    #     if cls._vaos.get(context_id) is None:
    #         cls._vaos[context_id] = {}
    #
    #     key = id(vertices)
    #     if cls._vaos[context_id].get(key) is None:
    #         cls._vaos[context_id][key] = GlVao(context_id, vertices, fmt, ins_data, ins_fmt)
    #
    #     return cls._vaos[context_id][key]
    #
    # @classmethod
    # def release_context(cls, context_id):
    #     vao_list = [vao.vao_id for vao in cls._vaos[context_id].values()]
    #     glDeleteVertexArrays(len(vao_list), vao_list)
    #     cls._vaos[context_id] = {}
    #
    # @classmethod
    # def release_vao(cls, context_id, vertices):
    #     key = id(vertices)
    #     vao = cls._vaos[context_id][key]
    #     glDeleteVertexArrays(1, [vao.vao_id])
    #     cls._vaos[context_id][key] = None

    # divisor =1 每实例更新 = 0每顶点更新

    def __init__(self, context_id, vertices, fmt=(3,2), usage=GL_STATIC_DRAW):
        self.context_id = context_id
        self.vertices = vertices
        self.fmt = fmt
        self.ins_vbo = None
        self.usage = usage

        self.vbo = GlVbo(context_id, vertices, usage)
        self.vao_id = glGenVertexArrays(1)
        glBindVertexArray(self.vao_id)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo.vbo_id)
        vert_len = sum(fmt)
        off_set = 0

        # 坐标点统一float32  即四字节  一般 前三位为xyz 四五位为uv
        for i,size in enumerate(fmt):
            glEnableVertexAttribArray(i)
            glVertexAttribPointer(i, size, GL_FLOAT, GL_FALSE, 4 * vert_len, ctypes.c_void_p(off_set))

            off_set += 4 * size

        GlContext.get_context(context_id).vao.append(self.vao_id)

    def reset_vbo_data(self, vertices):
        glBindVertexArray(self.vao_id)
        self.vbo.reset_data(vertices)

    def release(self):
        glDeleteVertexArrays(1, [self.vao_id])
        self.vbo.release()

        if self.ins_vbo:
            self.ins_vbo.release()