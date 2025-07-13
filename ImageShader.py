import random
from collections import deque


import cv2

from GlProgram import *
from ImageTool import adjust_img, cvt_color
from Setting import Setting
from VerticesTool import screen_vertices


class ImageShader:
    vertices = screen_vertices

    def __init__(self, shader_name, context_id, **kwargs):
        self.ae_output_texs = None
        self.program = GlProgram.get_program(shader_name, context_id)
        self.context_id = context_id
        self.main_tex = None
        self.time_count = 0.0
        self.time_step = 0.033
        self.end = False
        self.cap = None
        self.out_img_size = 0
        self.output_texs = None
        self.frame_cache = None
        self.fixed_img = None
        self.fixed_img_model = False
        self.fixed_frame_count = None

        self.after_eff = None

        self.ext_uniform = {}

        self.gl_state_cache = deque()

        self.width = 0
        self.height = 0
        self.cur_draw_num = 0

        self.get_max_draw()
        video_path = kwargs.get('video_path')

        if context_id:
            self.program.set_uniform(off_screen=1)
        elif video_path is not None:
            self.program.set_uniform(off_screen=0)
            self.cap = cv2.VideoCapture(video_path)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.create_main_tex(width, height)

        self.vao = None
        self.ins_vbo = None
        self.set_vao(self.vertices)

    def set_output(self, out_width, out_height):
        self.out_width, self.out_height = out_width, out_height
        self.out_img_size = self.out_width * self.out_height * 3
        self.output_texs = GlTextureArray(self.context_id, self.out_width, self.out_height, self.max_draw_ins,
                                        c_fmt=GL_RGBA8, is_down_tex=True)

        self.output_texs.bind_img_texture(0)

        self.set_resolution(out_width, out_height)

    def set_frame_cache(self, frame_cache):
        self.frame_cache = frame_cache
        w,h = frame_cache.width, frame_cache.height
        if w != self.width or h != self.height:
            self.create_main_tex(w,h)

        self.end = False

    def get_max_draw(self):
        if self.context_id:
            self.max_draw_ins = Setting.get('max_draw_ins')
        else:
            self.max_draw_ins = 1

        return self.max_draw_ins

    def set_vao(self, vertices):
        self.vao = GlVao(self.context_id, vertices)
        self.vertices = vertices

    def create_main_tex(self, width, height, pbo_num=2, tex_num=None):
        if self.main_tex:
            self.main_tex.release()

        self.width = width
        self.height = height

        tex_num = tex_num if tex_num is not None else self.max_draw_ins

        # 纹理数组
        self.main_tex = GlTextureArray(self.context_id, width, height, tex_num, use_pbo_num=pbo_num)

        # 单纹理
        # if self.main_tex is None:
        #     self.main_tex = GlTexture(self.context_id)
        # self.main_tex.resize_tex(width, height)

        self.program.location_tex('texture0', GL_TEXTURE0, 0)

    def set_resolution(self, w, h):
        self.resolution = (w, h)
        self.program.set_uniform(resolution=self.resolution)

    def set_fixed_img(self, img_path):
        self.fixed_img = adjust_img(img_path)
        self.fixed_img_model = True

    def set_fixed_frame_count(self, num):
        self.fixed_frame_count = num

    def get_next_img_from_cap(self):

        def read_frame():
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return read_frame()
            else:
                return frame

        cv_image = read_frame()

        if cv_image is not None:
            cv_image = cvt_color(cv_image)

        return cv_image

    def get_wait_draw_imgs(self):
        imgs = []
        if self.cap:
            while len(imgs) < self.max_draw_ins:
                img = self.get_next_img_from_cap()
                if img is not None:
                    imgs.append(img)
                else:
                    break
            imgs = np.stack(imgs, axis=0)
        elif self.frame_cache:
            imgs = self.frame_cache.get_frames()

        return imgs

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None

        if self.main_tex:
            self.main_tex.release()
            self.main_tex = None

        if self.vao:
            self.vao.release()
            self.vao = None

        if self.frame_cache:
            self.frame_cache.release()
            self.frame_cache = None

        if self.output_texs:
            self.output_texs.release()
            self.output_texs = None

    def add_ext_uniform(self, **kwargs):
        for k,v in kwargs.items():
            self.ext_uniform[k] = v

    def reset_state(self):
        self.time_count = 0.0
        self.end = False

    def set_ae_output_texs(self, texs):
        self.ae_output_texs = texs

    def up_tex_call_back(self):
        state = self.gl_state_cache.popleft()

        time_cost = state.get('time_cost')
        draw_num = state.get('draw_num')
        self.program.set_uniform(time=self.time_count)

        self.program.set_uniform(**self.ext_uniform)

        self.time_count += time_cost
        glBindVertexArray(self.vao.vao_id)
        self.cur_draw_num = draw_num
        if self.output_texs:
            self.output_texs.bind_img_texture(0)

        if self.after_eff:
            self.after_eff.draw_call(self)
        else:
            self.draw_call()

    def set_after_eff(self, ae):
        self.after_eff = ae

    def read_shader_result(self, read_size):
        output_text = self.ae_output_texs or self.output_texs
        if output_text:
            return output_text.down_tex_to_cpu(read_size)
        else:
            return None

    def cache_gl_state(self, imgs):
        img_num = len(imgs)
        if img_num > 0:
            self.gen_gl_state(img_num)

    def gen_gl_state(self, img_num):
        time_cost = self.time_step * img_num
        draw_num = img_num
        args = {"time_cost": time_cost, "draw_num": draw_num}
        self.gl_state_cache.append(args)

    def update_tex(self, imgs):
        if self.fixed_img_model:
            if self.fixed_img is not None:
                self.program.set_uniform(fixed_img=1)
                h, w = self.fixed_img.shape[:2]
                self.create_main_tex(w, h, 0, 1)

                self.main_tex.up_tex_immediately(self.fixed_img)

                self.fixed_img = None

            draw_num = self.max_draw_ins
            if self.fixed_frame_count is not None:
                if self.fixed_frame_count > self.max_draw_ins:
                    self.fixed_frame_count -= self.max_draw_ins
                else:
                    draw_num = self.fixed_frame_count
                    self.fixed_frame_count = 0

            self.main_tex.bind_tex()

            if draw_num > 0:
                self.gen_gl_state(draw_num)
                self.up_tex_call_back()
        else:
            self.main_tex.up_tex_arr_to_gl(imgs, self.up_tex_call_back)

    def shader_img(self):
        # glDepthMask(GL_FALSE)

        # glClearColor(0, 0, 0, 1.0)  # 设置背景颜色

        imgs = self.get_wait_draw_imgs()

        self.cache_gl_state(imgs)

        self.update_tex(imgs)

        data = self.read_shader_result(self.cur_draw_num * self.out_img_size)

        if self.cur_draw_num == 0 and data is None and len(imgs) == 0:
            self.end = True

        self.cur_draw_num = 0

        return data

    def draw_call(self):
        pass