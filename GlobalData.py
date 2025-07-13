import math
import os

import random
from pathlib import Path

from AudioTool import read_srt_file
from FileTool import load_json_file, save_json_file


class GlobalData:
    _instance = None


    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.init_data()
        return cls._instance

    def __init__(self):
        pass

    def set_save_path(self, path):
        self.save_path = path
        self.voice_clip_path = self.save_path + '/声音片段'
        self.voice_path = self.save_path + '/合成配音.wav'
        self.srt_path = self.save_path + '/音频字幕.srt'
        self.video_path = self.save_path + '/无声视频.mp4'
        self.finnal_audio = self.save_path + '/背景音乐.wav'

        dir_name = Path(path).name
        self.finnal_video = self.save_path + f'/{dir_name}.mp4'
        self.imgs_path = self.save_path + '/图片'
        self.shot_path = self.save_path + '/shots.json'

        self.temp_bgm = self.save_path + '/变奏bgm.wav'

        self.temp_srt_path = os.path.abspath(self.save_path + '/temp.srt')

        self.save_data()

    def init_data(self):

        self.bgm_path = None
        self.bgm_volume = 0.35
        self.bgm_speed = 1
        self.bgm_pitch = 0
        self.bgm_setting = None

        self.voice_pitch = 0
        self.voice_volume = 1.4
        self.voice_speed = 1.3
        self.cut_silent = True
        self.enhan_vocal = True

        self.voice_clone_path = None

        self.img_dir = None
        self.srt_data = None

        self.video_paths = None
        self.eff_dict = {}
        self.video_resolution = None

        self.replace_face_manage = None

        self.attach_srt = True
        self.video_fps = 30

        self.save_path = None

        self.load_op_cache()

        if self.save_path is None:
            base_dir = Path.home() / 'Desktop'
            # self.save_path = get_increment_dir(base_dir, "生成目录")
            self.save_path = f'{base_dir}/{'生成目录'}'
            os.makedirs(self.save_path, exist_ok=True)

        self.set_save_path(self.save_path)

    def load_op_cache(self):
        data_path = 'op_cache.json'

        if os.path.isfile(data_path):
            data = load_json_file(data_path)
            self.save_path = data.get('save_path')
            self.bgm_volume = data.get('bgm_volume')
            self.bgm_speed = data.get('bgm_speed')
            self.bgm_pitch = data.get('bgm_pitch')

            self.voice_pitch = data.get('voice_pitch')
            self.voice_volume = data.get('voice_volume')
            self.voice_speed = data.get('voice_speed')

            self.cut_silent = data.get('cut_silent')
            self.enhan_vocal = data.get('enhan_vocal')


    def save_data(self):
        data = {'save_path':self.save_path, 'bgm_volume':self.bgm_volume,
                'bgm_speed':self.bgm_speed, 'bgm_pitch':self.bgm_pitch,
                'voice_pitch':self.voice_pitch, 'voice_volume':self.voice_volume,
                'voice_speed':self.voice_speed, 'enhan_vocal': self.enhan_vocal,
                'cut_silent':self.cut_silent}
        save_json_file('op_cache.json', data)

    def get_voice_setting(self):
        setting = {'cut_silent': self.cut_silent, 'enhan_vocal': self.enhan_vocal,
                   'speed': self.voice_speed, 'volume': self.voice_volume,
                   'pitch': self.voice_pitch}

        return setting

    def read_srt_data(self):
        if os.path.isfile(self.srt_path):
            self.srt_data = read_srt_file(self.srt_path)
        else:
            if os.path.isfile(self.temp_srt_path):
                self.srt_data = read_srt_file(self.temp_srt_path)
            else:
                self.srt_data = None

    def get_random_active_eff(self):
        filter_items = [eff for eff, flag in self.eff_dict.items() if flag ]
        return random.choice(filter_items) if filter_items else 'wuxiaoguo'

    def get_eff_length(self):
        return len([eff for eff, flag in self.eff_dict.items() if flag])

    def get_random_video(self):
        return random.choice(self.video_paths) if self.video_paths else None

    def get_adjust_resolustion(self, width, height):
        if self.video_resolution is None:
            return width, height

        w, h = width, height
        if width / height > self.video_resolution:
            h = math.floor(width / self.video_resolution)
        else:
            w = math.floor(height * self.video_resolution)

        return w, h