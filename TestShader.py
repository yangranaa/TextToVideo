import json
import math
import os
import random
import re
import sys
import threading
import time
from collections import deque
from urllib.parse import urlsplit

import cv2
import decord
import numpy as np
import requests
from OpenGL.GL import *
from PyQt6.QtCore import QRegularExpression

import VerticesTool
# print("fc2fc2", id(fc2), sys.getrefcount(fc2) - 1)
from FrameCache import FrameCache
from GlProgram import GlVao, GlProgram, GlTextureArray

paths = [r"C:\Users\Administrator\Desktop\jianying.mp4",r"C:\Users\Administrator\Desktop\ceshi2.mp4"]


path = r"C:\Users\Administrator\Desktop\ttest\ttest.mp4"

cap = cv2.VideoCapture(path)

def read_frame(idx):
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ret, frame = cap.read()
    if ret:
        return frame


for i in range(10, 50):
    print(i)

# for i in range(0, 400, 1):
#     frame = read_frame(i)
#     cv2.imshow(f'{i}', frame)
#     cv2.waitKey(0)

urls = ['http://sgw-dx.xf-yun.com/api/v1/spkdesk2/cd6268ac-e740-40d3-9bdb-d603f41d6f66.jpg?authorization=c2ltcGxlLWp3dCBhaz1zcGtkZXNrMmQ0YzM1YjBjO2V4cD0xOTA1MjM5MDU5O2FsZ289aG1hYy1zaGEyNTY7c2lnPUdPRE5HMVEwZUwwUG93T0VLVE14M0o0VFl5dEljZVJteHhFMGFHc0RaTFE9&x_location=7YfQJjZB7uKtx2GYyYUleXD=','http://sgw-dx.xf-yun.com/api/v1/spkdesk2/0d588142-54ae-4701-afdd-142d1a9911c3.jpg?authorization=c2ltcGxlLWp3dCBhaz1zcGtkZXNrMmQ0YzM1YjBjO2V4cD0xOTA1MjM5MDY0O2FsZ289aG1hYy1zaGEyNTY7c2lnPTlWWHdOR1d3dW1MYTRMdDJ1aDU5Vi83QXVQM0lONHBZZjltR0RtZ2lyb1U9&x_location=7YfQJjZB7uKtx2GYyYUleXD=']



#
# for i, url in enumerate(urls):
#     download_image(url, f"{i}.jpg")













# ssss = "莫天骄撒大苏打莫天骄"
#
# pattern = QRegularExpression(f"莫天骄")  # 使用单词边界匹配
# match_iterator = pattern.globalMatch(ssss)
#
# while match_iterator.hasNext():
#     match = match_iterator.next()
#     start = match.capturedStart()
#     length = match.capturedLength()
#     print(start, length)



#
#



# img_num = 900
# batch_size = 120
# start_time = time.time()
#
# group_num = math.floor(img_num/batch_size)
# last_num = img_num - group_num * batch_size
#
# cap = cv2.VideoCapture(paths[1])
# width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
# img_size = int(width * height * 3)
#
# def read_frame():
#     ret, frame = cap.read()
#     if not ret:
#         cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
#         return read_frame()
#     else:
#         return frame
#
#
# img_list = np.empty((img_num, height, width, 3),dtype=np.uint8)
#
# for i in range(img_num):
#     img_list[i] = read_frame()

# def load_fun():
#     vr = decord.VideoReader(paths[1], ctx=decord.cpu(0))
#     cache = deque()
#     for i in range(group_num):
#         batch_img = vr[i*batch_size: (i+1) * batch_size].asnumpy()
#         cache.append(batch_img)
#
#     if last_num > 0:
#         batch_img = vr[-last_num -1: -1].asnumpy()
#         cache.append(batch_img)
#
# fc = FrameCache(paths[1])
# fc.set_pos(0,img_num)
# fc.start_load(batch_size)
# fc.load_thread.join()
#
#
# end_time = time.time()
#
#
# print("每张用时", (end_time-start_time)/img_num, "总用时", end_time-start_time)

# def save_fun(data):
#     off_set = 0
#     size = 1080 * 1920 * 3
#
#     for i in range(500):
#         dict[i] = data[off_set:off_set + size]
#         off_set += size
#         print("data", id(data), sys.getrefcount(data) - 1)
#
# save_fun(test_data)
#
#
# off_set = 0
# def get_fun():
#     for i in range(100):
#         data = dict[i]
#         dict[i] = None
#
#     return data
#
# for i in range(5):







# print("lasttt", id(test_data), sys.getrefcount(test_data) - 1)
#
#
#
#
#
# input("bbbb")
#
# input("bbbb")


#
#
#         #
#         # fc3.get_frames()
#
#         input("aa")
#
# tf = threading.Thread(target=thread_fun)
# tf.start()




#
#
# time.sleep(100)

# num = len(vr)
# for i in range(num):
#     img = vr[i]
#
