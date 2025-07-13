import math
import subprocess
import sys
import threading

import ffmpeg
from PyQt6.QtCore import QObject, pyqtSignal

from AudioTool import variation_audio, get_audio_duration
from FileTool import delete_file
from GlobalData import GlobalData
from HardwareDetection import HardwareDetection
from ImageTool import resize_img, decode_img
from OffScreenRender import OffScreenRender
from Setting import Setting
from ShotData import ShotData
from VideoTool import get_frame_size


class QtSignals(QObject):
    """定义信号的类"""
    finished = pyqtSignal(dict)

class VideoWrite:

    def __init__(self, parent):
        self.audio_stream = None

        parent.finished.connect(self.release)

        duration_secound = get_audio_duration(GlobalData().voice_path)

        frame_count = math.ceil(GlobalData().video_fps * duration_secound)

        if len(ShotData.shot_datas) > 0:
            w, h = 1024, 768
            # h, w = resize_img(decode_img(ShotData.shot_datas[0].img_path)).shape[:2]
        else:
            w, h, _ = get_frame_size(GlobalData().video_paths[0])

        adjus_w, adjus_h = GlobalData().get_adjust_resolustion(w, h)

        self.signals = QtSignals()
        self.width = adjus_w
        self.height = adjus_h
        self.fps = GlobalData().video_fps
        self.count = 0
        self.codecs = ['h264_nvenc', 'h264_amf', 'h264_qsv', 'libx264']
        self.sel_codec = 0
        self.write_proc = None
        self.end = threading.Event()

        self.frame_count = frame_count
        self.off_screen_render = OffScreenRender(GlobalData().video_paths, adjus_w, adjus_h, frame_count)


    def init_ffmpeg_write(self):

        self.video_path = GlobalData().video_path
        voice_path = GlobalData().voice_path
        bgm_path = GlobalData().bgm_path
        srt_path = GlobalData().srt_path
        self.finnal_path = GlobalData().finnal_video

        delete_file(self.video_path)
        delete_file(self.finnal_path)

        duration = self.frame_count / self.fps

        self.video_stream = ffmpeg.input('pipe:', format='rawvideo', pix_fmt='rgb24', s=f'{self.width}x{self.height}',
                                         r=self.fps)
        if GlobalData().attach_srt:
            # 添加硬字幕滤镜
            self.video_stream = self.video_stream.video.filter(
                'subtitles',
                filename=srt_path,
                force_style="FontSize=20,Alignment=2,MarginV=40"  # 可选：FontName=SimHei覆盖字幕样式
            )

        self.audio_stream = ffmpeg.input(voice_path)

        if bgm_path:
            bgm_setting = {'volume': GlobalData().bgm_volume,
                           'speed': GlobalData().bgm_speed,
                           'pitch': GlobalData().bgm_pitch,
                           'duration': duration}

            variation_audio(GlobalData().bgm_path, GlobalData().finnal_audio, **bgm_setting)

            bgm_input = ffmpeg.input(GlobalData().finnal_audio)

            self.audio_stream = ffmpeg.filter(
                [bgm_input.audio, self.audio_stream.audio],
                'amix',
                duration='shortest',
            )

            # self.audio_stream = self.audio_stream.filter('dynaudnorm')

        self.set_ffmpeg_write(self.codecs[self.sel_codec])


    def set_ffmpeg_write(self, codec):

        fast_codec = HardwareDetection.get_fast_encoder(codec)


        output = ffmpeg.output(self.video_stream, self.audio_stream, self.finnal_path, **fast_codec)

        if not Setting.get('debug'):
            output = output.global_args('-loglevel', 'quiet')

        # 配置进程参数
        # startupinfo = subprocess.STARTUPINFO()
        # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # startupinfo.wShowWindow = subprocess.SW_HIDE

        cmd = output.compile(overwrite_output=True)

        self.write_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                                           # startupinfo=startupinfo,
                                           # creationflags=subprocess.CREATE_NO_WINDOW,



    def try_write_frame(self, frame):

        try:
            self.write_proc.stdin.write(frame)
        except Exception as e:
            self.sel_codec += 1
            self.set_ffmpeg_write(self.codecs[self.sel_codec])
            self.try_write_frame(frame)

    def write_frames(self):
        # self.gen_start = time.time()

        try:
            self.init_ffmpeg_write()
        except Exception as e:
            self.signals.finished.emit({'error': e.__str__()})
            self.release()
            return

        self.off_screen_render.start_render_thread()

        frame = self.off_screen_render.get_frame()
        while frame is not None:
            if self.end.is_set():
                break

            self.try_write_frame(frame)

            self.count += 1
            frame = self.off_screen_render.get_frame()

            self.signals.finished.emit({"value": self.count, "total_value": self.frame_count, "finnal_packaging":True})

        self.release()

        self.signals.finished.emit({"end": True})

    def start_write_thread(self):
        write_thread = threading.Thread(target=self.write_frames)
        write_thread.start()

    def release(self):
        self.end.set()

        if self.write_proc:
            self.write_proc.stdin.close()
            self.write_proc.wait()

        if self.off_screen_render:
            self.off_screen_render.stop_render_thread()


        # end_time = time.time()
        # print(f"写入结束用时{end_time - self.gen_start} 均时{(end_time-self.gen_start) / self.count}=={self.count}")