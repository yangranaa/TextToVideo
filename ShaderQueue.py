import math

from AfterEffShader import AfterEffShader
from ShotEffConfig import get_enter_eff_config
from BrokenShader import BrokenShader
from FaceReplace import FaceReplace
from GlobalData import GlobalData
from MoveShader import MoveShader
from NormalShader import NormalShader
from TurnPageShader import TurnPageShader


class ShaderManager:
    @classmethod
    def create_shader(cls, context_id, eff, video_path=None):
        if eff == 'suiping':
            shader = BrokenShader(context_id, video_path=video_path)
        elif eff == 'face_replace':
            shader = FaceReplace(context_id, video_path=video_path)
        elif eff == 'yidong':
            shader = MoveShader(context_id, video_path=video_path)
        elif eff == 'fanye':
            shader = TurnPageShader(context_id, video_path=video_path)
        else:
            shader = NormalShader(eff, context_id, video_path=video_path)

        return shader

    @classmethod
    def create_shader_queue(cls, context_id, **kwargs):

        eff = kwargs.get('eff')
        enter_eff = kwargs.get('enter_eff')
        video_path = kwargs.get('video_path')
        frame_count = kwargs.get('frame_count')

        view_fbo = kwargs.get('view_fbo', 0)
        resolution = kwargs.get('resolution')

        shader_queue = ShaderQueue(context_id, view_fbo, resolution)
        if enter_eff:
            shader = cls.create_shader(context_id, enter_eff, video_path)
            shader_queue.push_shader(shader)

            eff_config = get_enter_eff_config(enter_eff)
            enter_frame_count = math.ceil(GlobalData().video_fps * eff_config[2])

            if frame_count:
                if frame_count > enter_frame_count:
                    frame_count -= enter_frame_count
                    shader.set_fixed_frame_count(enter_frame_count)
                else:
                    shader.set_fixed_frame_count(frame_count)
                    return shader_queue
            else:
                shader.set_fixed_frame_count(enter_frame_count)

        shader = cls.create_shader(context_id, eff, video_path)
        shader_queue.push_shader(shader)

        if frame_count:
            shader.set_fixed_frame_count(frame_count)

        return shader_queue

class ShaderQueue:

    def __init__(self, context_id, view_fbo, resolution):
        self.resolution = resolution
        self.context_id = context_id
        self.view_fbo = view_fbo
        self.queue = []

        self.after_eff = None
        self.after_eff_name = None

    def push_shader(self, imgshader):
        self.queue.append(imgshader)

    def clear_queue(self):
        for shader in self.queue:
            shader.release()

        self.queue.clear()

        self.release()

    def release(self):
        if self.after_eff:
            self.after_eff.release()
            self.after_eff = None

    def shader_queue(self):
        if self.after_eff_name:
            if self.after_eff is None:
                self.after_eff = AfterEffShader(self.context_id, self.view_fbo, self.resolution, [self.after_eff_name])
            self.after_eff_name = None

        data = None
        while len(self.queue) > 0:
            shader = self.queue[0]
            shader.set_after_eff(self.after_eff)

            data = shader.shader_img()
            if shader.end:
                self.queue.pop(0)
                shader.release()
            else:
                break

        if len(self.queue) == 0:
            self.release()

        return data

    def get_active_shader(self):
        if len(self.queue) > 0:
            return self.queue[0]

    def set_fixed_img(self, img):
        for shader in self.queue:
            shader.set_fixed_img(img)

    def set_output(self, width, height):
        self.resolution = (width, height)
        for shader in self.queue:
            shader.set_output(width, height)

    def set_resolution(self, w, h):
        self.resolution = (w, h)
        for shader in self.queue:
            shader.set_resolution(w, h)

    def add_ext_uniform(self, **kwargs):
        for shader in self.queue:
            shader.add_ext_uniform(**kwargs)

    def add_after_eff(self, eff):
        self.after_eff_name = eff
