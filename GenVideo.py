# import math
# import os
# import random
# import time
#
# import cv2
# import ffmpeg
# import numpy as np
# from OpenGL.GL import *
#
# from PyQt5.QtCore import QThread, pyqtSignal, QRunnable
# from PyQt5.QtGui import QOffscreenSurface, QOpenGLContext, QOpenGLFramebufferObject
#
# from AudioTool import get_audio_duration, variation_audio
# from BrokenShader import BrokenShader
# from FileTool import delete_file
# from GlobalData import GlobalData
# from HardwareDetection import HardwareDetection
# from NormalShader import NormalShader
# from ObjTool import print_attr, print_fun
# from ShaderQueue import ShaderQueue
#
# OUT_TIME_PREFIX = b"out_time_"
# MULTIPLIER = 1e-6
#
# class GenVideo(QThread):
#
#     finished = pyqtSignal(dict)
#
#     def __init__(self):
#         super().__init__()
#         self.fps = 30
#         self.fbo = None
#         self.shader_queue = ShaderQueue()
#         self.video_writer = None
#         self.shader_count = 0
#         self.context_id = 0
#
#         self.gl_context = None
#         self.surface = None
#
#     def emit_ffmpeg_progress_data(self, process, total_duration, step_name):
#         for line in process.stdout:
#             if line[:9] == OUT_TIME_PREFIX:
#                 value = line[12:-1]
#                 try:
#                     value_int = int(value) * MULTIPLIER
#                     if value_int <= total_duration:
#                         self.finished.emit(
#                             {"value": math.floor(value_int), "total_value": math.ceil(total_duration),
#                              step_name: True})
#                 except (IndexError, ValueError):
#                     pass
#
#     # def concate_video(self):
#     #     out_path = GlobalData().video_path
#     #
#     #     delete_file(out_path)
#     #
#     #     duration_secound = get_audio_duration(GlobalData().voice_path)
#     #     dur_count = 0
#     #     file_list = []
#     #     while dur_count < duration_secound:
#     #         file = GlobalData().get_random_video()
#     #         probe = ffmpeg.probe(file)
#     #         video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
#     #         if video_stream:
#     #             dur_count += float(video_stream['duration'])
#     #             file_list.append(file)
#     #         else:
#     #             raise ValueError(f"无法获取视频时长: {file}")
#     #
#     #     input_list = [ffmpeg.input(file) for file in file_list]
#     #     joined = ffmpeg.concat(*input_list, v=1)
#     #     cut_video = joined.trim(start=0, duration=duration_secound)
#     #
#     #     output = cut_video.output(out_path)
#     #     output = output.global_args("-progress", "pipe:1", "-hide_banner", "-nostats", '-loglevel', 'verbose')  # 输出进度到 stdout
#     #     process = output.run_async(overwrite_output=True, pipe_stdout=True)
#     #
#     #     self.emit_ffmpeg_progress_data(process, duration_secound, 'fill_video')
#
#     def finnal_pack(self):
#
#
#
#
#
#
#         audio_stream = None
#         #
#         #
#         # if bgm_path:
#         #     bgm_setting = {'volume': GlobalData().bgm_volume,
#         #                    'speed': GlobalData().bgm_speed,
#         #                    'pitch': GlobalData().bgm_pitch,
#         #                    'duration': duration}
#         #
#         #     variation_audio(GlobalData().bgm_path, GlobalData().finnal_audio, **bgm_setting)
#         #
#         #     bgm_input = ffmpeg.input(GlobalData().finnal_audio)
#         #
#         #     audio_stream = ffmpeg.filter(
#         #         [bgm_input.audio, voice_input.audio],
#         #         'amix',
#         #         duration='shortest'
#         #     )
#         # else:
#         #     audio_stream = voice_input
#         #
#         # fast_codec = HardwareDetection.get_fast_encoder()
#         #
#         # output = ffmpeg.output(video_stream, audio_stream, finnal_path,
#         #                               vcodec=fast_codec,  # 视频编码器
#         #                               acodec='aac',  # 音频编码器
#         #                               # crf='18'
#         #                               )
#         #
#         # # force_style = "FontName=Arial,FontSize=24,FontColor=white"
#         #
#         # output = output.global_args("-progress", "pipe:1", "-hide_banner", "-nostats", '-loglevel','verbose')
#         # process = output.run_async(overwrite_output=True, pipe_stdout=True)
#         #
#         # self.emit_ffmpeg_progress_data(process, duration, 'finnal_packaging')
#
#     def run(self):
#
#         delete_file(GlobalData().video_path)
#
#         # eff = GlobalData().get_random_active_eff()
#         # if eff == 'wuxiaoguo':
#         #     self.concate_video()
#         # else:
#         self.reset_context()
#         self.fbo.bind()
#         self.reset_video_writer()
#         self.random_shader_queue()
#
#
#
#         self.write_frames()
#         self.release_shader()
#
#         self.finnal_pack()
#         self.finished.emit({"write_end": True})
#
#
#
#     def random_shader_queue(self):
#         self.shader_queue.clear_queue()
#         duration_secound = get_audio_duration(GlobalData().voice_path)
#         self.frame_count = math.ceil(self.fps * duration_secound)
#         frame_count = self.frame_count
#
#         while frame_count > 0:
#             random_eff = GlobalData().get_random_active_eff()
#             random_video = GlobalData().get_random_video()
#
#
#
#
#             if random_frame > 9000:
#                 random_frame = random.randint(4500, 9000)
#
#             shader = None
#             if random_eff == 'suiping':
#                 shader = BrokenShader(self.context_id, video_path=random_video)
#             else:
#                 shader = NormalShader(random_eff, self.context_id, video_path=random_video)
#
#             shader.set_frame_count(random_frame)
#             frame_count -= random_frame
#
#             self.shader_queue.push_shader(shader)
#
#
#
#
#
#
#
