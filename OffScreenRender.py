import math
import random
import threading
import time

import psutil
from OpenGL.GL import *

from FrameCache import FrameCache
from GlProgram import GlFbo, GlContext
from GlobalData import GlobalData
from MyLog import MyLog
from Setting import Setting
from ShaderQueue import ShaderManager
from ShotData import ShotData
from VideoTool import get_frame_size


class OffScreenRender:

    def __init__(self, video_paths, width, height, frame_count):

        self.width = width
        self.height = height
        self.img_size = self.width * self.height * 3
        self.frame_count = frame_count
        self.max_cache = Setting.get('max_draw_ins') * 10
        self.handout_count = 0
        self.shader_ptr = 0
        self.read_ptr = 0
        self.stop_thread = threading.Event()
        self.video_paths = video_paths
        self.clip_less_frame = Setting.get('clip_less_frame')
        self.clip_max_frame = Setting.get('clip_max_frame')

        _init_dict = {i: None for i in range(self.frame_count)}
        self.frame_dict = dict(_init_dict)

        self.clip_que = []
        if len(ShotData.shot_datas) > 0:
            self.gen_clip_que()
        else:
            self.random_clips()

        self.cur_shader = None
        self.pre_shader = None

        self.pre_que = None
        self.cur_que = None

        self.cur_clip_data = None
        self.pre_data = None
        self.pre_fc = None

    def gen_clip_que(self):
        srt_data = GlobalData().srt_data

        self.clip_que = []

        end_idx = 0
        for shot_data in ShotData.shot_datas:
            end_idx += len(shot_data.line_list)

            end_frame = math.ceil(srt_data[end_idx - 1][1][1] * GlobalData().video_fps)

            clip_data = {}
            clip_data['img'] = shot_data.img_path
            clip_data['end_frame'] = end_frame
            clip_data['eff'] = shot_data.eff
            clip_data['enter_eff'] = shot_data.enter_eff
            clip_data['after_eff'] = shot_data.after_eff
            self.clip_que.append(clip_data)

    def random_clips(self):
        self.clip_data = {}
        total_frame = 0
        for video_path in self.video_paths:
            w, h, f = get_frame_size(video_path)
            if self.clip_data.get((w, h)) is None:
                self.clip_data[(w, h)] = []
            self.clip_data[(w, h)].append([video_path, f])
            total_frame += f

        clip_frame_count = 0
        self.clip_que = []

        shader_eff = GlobalData().get_random_active_eff()

        for wh, video_list in self.clip_data.items():
            list_frame_count = sum(tup[1] for tup in video_list)
            cut_frame = math.ceil(self.frame_count * list_frame_count/total_frame)

            while cut_frame > 0:
                ran_video = random.choice(video_list)
                if ran_video[1] <= self.clip_less_frame:
                    start_pos = 0
                else:
                    start_pos = random.randint(0, ran_video[1] - self.clip_less_frame - 1)

                if ran_video[1] - start_pos > self.clip_max_frame:
                    end_pos = start_pos + random.randint(self.clip_less_frame, self.clip_max_frame)
                else:
                    end_pos = ran_video[1]

                frame_count = end_pos - start_pos
                if frame_count > cut_frame:
                    over_num = frame_count - cut_frame
                    end_pos -= over_num
                    frame_count -= over_num

                clip_frame_count += frame_count
                clip_data = {}
                clip_data['width'] = wh[0]
                clip_data['height'] = wh[1]
                clip_data['video'] = ran_video[0]
                clip_data['start_pos'] = start_pos
                clip_data['end_pos'] = end_pos
                clip_data['frame_count'] = clip_frame_count
                clip_data['eff'] = shader_eff

                self.clip_que.append(clip_data)
                cut_frame -= frame_count

        random.shuffle(self.clip_que)



    def prepare_next_clip(self):
        return_condition = False

        return_condition |= self.pre_data is not None

        return_condition |= len(self.clip_que) <= 0

        if len(ShotData.shot_datas) <= 0:
            return_condition |= self.cur_shader is not None and self.cur_shader.frame_cache and not self.cur_shader.frame_cache.stop_event.is_set()

        if return_condition:
            return

        self.pre_data = self.clip_que.pop(0)

        shader_que_args = None

        if len(ShotData.shot_datas) > 0:
            shader_que_args = self.pre_data

            if self.cur_clip_data is None:
                shader_que_args['frame_count'] = self.pre_data.get('end_frame')

            else:
                shader_que_args['frame_count'] = self.pre_data.get('end_frame') - self.cur_clip_data.get('end_frame')

        else:
            if self.cur_clip_data is None:
                self.pre_shader = ShaderManager.create_shader(self.context_id, self.pre_data.get('eff'))
                self.pre_shader.set_output(self.width, self.height)

        if shader_que_args:
            self.pre_que = ShaderManager.create_shader_queue(self.context_id, **shader_que_args)
            self.pre_que.set_fixed_img(self.pre_data.get('img'))
            self.pre_que.set_output(self.width, self.height)

            if self.pre_data.get("after_eff"):
                self.pre_que.add_after_eff(self.pre_data.get("after_eff"))


        if self.pre_data.get('video'):
            self.pre_fc = FrameCache(self.pre_data.get('video'))
            self.pre_fc.set_pos(self.pre_data.get('start_pos'), self.pre_data.get('end_pos'))

            if self.pre_shader is not None:
                self.pre_fc.start_load(self.pre_shader.get_max_draw())
            elif self.cur_shader is not None:
                self.pre_fc.start_load(self.cur_shader.get_max_draw())


    def charge_cur_shader(self):

        self.cur_clip_data = self.pre_data
        self.pre_data = None

        if self.pre_shader is not None:
            if self.cur_shader:
                self.cur_shader.release()

            self.cur_shader = self.pre_shader
            self.pre_shader = None

        if self.pre_que is not None:
            if self.cur_que:
                self.cur_que.clear_queue()

            self.cur_que = self.pre_que
            self.pre_que = None

        if self.pre_fc is not None:
            self.cur_shader.set_frame_cache(self.pre_fc)
            self.pre_fc = None
            self.cur_shader.reset_state()


    def check_shader_process(self):

        end = self.check_shader_end()
        if end:

            while self.pre_data is None:
                self.prepare_next_clip()

            self.charge_cur_shader()

        else:
            self.prepare_next_clip()

    def reset_gl_context(self):
        # 上下文id
        self.context_id = 100

        GlContext.get_context(self.context_id)
        GlFbo(self.context_id, self.width, self.height)
        glViewport(0, 0, self.width, self.height)


    def use_fbo(self, num):
        self.cur_fbo = 0
        self.fbos = []
        for i in range(num):
            fbo = GlFbo(self.context_id, self.width, self.height)
            self.fbos.append(fbo)

    def get_cur_fbo(self):
        return self.fbos[self.cur_fbo]

    def get_next_fbo(self):
        return self.fbos[(self.cur_fbo + 1)%len(self.fbos)]

    def step_fbo_id(self):
        self.cur_fbo += 1
        self.cur_fbo = self.cur_fbo % len(self.fbos)


    def shader_img(self):

        if self.cur_shader:
            data = self.cur_shader.shader_img()
        else:
            data = self.cur_que.shader_queue()

        return data

    def check_shader_end(self):
        if len(ShotData.shot_datas) > 0:
            end = self.cur_que is None or self.cur_que.get_active_shader() is None
        else:
            end = self.cur_shader is None or self.cur_shader.end

        return end

    def render(self):
        self.reset_gl_context()

        # cur_fbo = self.get_cur_fbo().fbo_id
        # glBindFramebuffer(GL_FRAMEBUFFER, cur_fbo)
        # glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_shader_process()

        while self.shader_ptr < self.frame_count:

            if self.stop_thread.is_set():
                break

            if not self.is_can_read():
                MyLog.info("渲染暂停", self.shader_ptr, self.read_ptr)
                time.sleep(0.2)
                continue

            data = None
            if self.check_shader_end():
                self.check_shader_process()
            else:
                data = self.shader_img()

            if data is not None:
                self.save_arry_img(data)

        MyLog.info("渲染完毕", self.shader_ptr, self.frame_count, self.read_ptr)
        # pixels = data[offset:img_size].reshape(self.height, self.width, 3)
        # cv2.imshow('down', pixels)
        # cv2.waitKey(0)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        GlContext.release_context(self.context_id)

    def save_arry_img(self, data):
        off_set = 0

        while off_set < len(data):
            img_data = data[off_set:off_set + self.img_size]
            self.frame_dict[self.shader_ptr] = img_data
            self.shader_ptr += 1
            off_set += self.img_size

        self.check_shader_process()


    def is_can_read(self):
        cache_num = self.shader_ptr - self.read_ptr
        if cache_num > self.get_max_cache():
            return False
        return True

    def get_max_cache(self):
        memory_info = psutil.virtual_memory()
        min_num = math.floor(memory_info.free * 0.5 / 6220800)
        min_num = self.max_cache if min_num > self.max_cache else min_num
        return min_num

    def get_frame(self):
        if self.read_ptr == self.frame_count:
            return None

        frame_data = self.frame_dict.get(self.read_ptr)
        if frame_data is None:
            if self.stop_thread.is_set():
                return None

            MyLog.info("等待绘制图==========================", self.read_ptr, self.frame_count)
            time.sleep(1)
            return self.get_frame()
        else:
            self.frame_dict[self.read_ptr] = None
            self.read_ptr += 1
            return frame_data

    def start_render_thread(self):
        self.render_thread = threading.Thread(target=self.render)
        self.render_thread.start()

    def stop_render_thread(self):
        self.stop_thread.set()

