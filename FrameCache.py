import math
import sys
import threading
import time
from collections import deque

import decord
import psutil

from MyLog import MyLog
from ObjTool import print_trace_back


class FrameCache:

    def __init__(self, video_path):
        try:
            self.vr = decord.VideoReader(video_path, ctx=decord.gpu(0))
        except Exception as e:
            self.vr = decord.VideoReader(video_path, ctx=decord.cpu(0))

        self.max_cache = 4
        self.start_pos = 0
        self.end_pos = 0
        self.batch_size = 0
        self.stop_event = threading.Event()

        self.frame_count = len(self.vr)

        self.cache_frames = deque()


    def set_pos(self, start_pos, end_pos):
        self.start_pos = start_pos
        self.end_pos = end_pos

        shape = self.vr[start_pos].shape
        self.width, self.height = shape[1], shape[0]
        self.frame_size = self.width * self.height * 3


    def start_load(self, batch_size):
        self.batch_size = batch_size
        self.load_thread = threading.Thread(target=self.load_fun)
        self.load_thread.start()

        # self.load_fun()


    def load_fun(self):
        while not self.stop_event.is_set():

            has_img = self.batch_read()
            if not has_img:
                self.stop_event.set()
                self.vr = None
                break


    def batch_read(self):
        if self.start_pos >= self.end_pos:
            return False

        read_num = min(self.batch_size, self.end_pos - self.start_pos)
        frames = self.vr[self.start_pos: self.start_pos + read_num].asnumpy()
        self.start_pos += read_num

        self.cache_frames.append(frames)

        return True

    def get_frames(self):
        if len(self.cache_frames) > 0:
            imgs = self.cache_frames.popleft()
            return imgs
        else:
            if not self.stop_event.is_set():
                MyLog.info("等待读图")
                time.sleep(0.2)
                return self.get_frames()
            else:
                return []

    # def get_max_cache(self):
    #     memory_info = psutil.virtual_memory()
    #     min_num = math.floor(memory_info.free * 0.5 / self.frame_size)
    #     min_num = min(self.max_cache, min_num)
    #     return min_num



    def release(self):
        self.stop_event.set()

        self.vr = None

        self.cache_frames.clear()

