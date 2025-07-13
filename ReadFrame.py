#
# import math
# import random
# import threading
# import time
#
# import cv2
# import decord
# import psutil
#
# from MyLog import MyLog
#
#
# class ReadFrame:
#
#     def __init__(self, video_paths, write_frame_count):
#         super().__init__()
#         self.on_read = True
#         self.sleep_time = 0.1
#         self.max_cache = 600
#         self.max_thread = 1
#         self.threads = {}
#         self.stop_thread = False
#         self.video_paths = video_paths
#         # self.lock = threading.Lock()
#
#         self.clip_less_frame = 600
#         self.clip_max_frame = 900
#
#         self.write_frame_count = write_frame_count
#
#         # decord
#         self.cur_dvr = None
#         self.reset_work_decord()
#
#         self.cache_frame_ptr = 0
#         self.get_frame_ptr = 0
#
#     def reset_work_decord(self):
#         if self.cur_dvr:
#             del self.cur_dvr
#
#         video_path = random.choice(self.video_paths)
#         try:
#             vr = decord.VideoReader(video_path, ctx=decord.gpu(0))
#         except Exception as e:
#             vr = decord.VideoReader(video_path, ctx=decord.cpu(0))
#
#         self.cur_dvr = [vr, 0, 0]
#
#         total = len(self.cur_dvr[0])
#         if total < self.clip_less_frame:
#             self.cur_dvr[1] = 0
#         else:
#             self.cur_dvr[1] = random.randint(0, total - self.clip_less_frame - 1)
#
#     def batch_read_decord(self, batch_size=32):
#         total = len(self.cur_dvr[0])
#         read_size = batch_size
#         reset_decord = False
#         if self.cur_dvr[1] + batch_size > total:
#             reset_decord = True
#             read_size = total - self.cur_dvr[1]
#
#         batch = self.cur_dvr[0][self.cur_dvr[1]:self.cur_dvr[1] + read_size].asnumpy()  # 若用GPU需转换为numpy
#         self.cur_dvr[1] += read_size
#
#         self.cur_dvr[2] += read_size
#
#         if self.cur_dvr[2] > self.clip_max_frame:
#             reset_decord = True
#
#         for i in range(read_size):
#             self.frame_dict[self.cache_frame_ptr] = batch[i]
#             self.cache_frame_ptr +=1
#
#         if reset_decord:
#             self.reset_work_decord()
#
#     def read_frame(self):
#         while self.cache_frame_ptr < self.write_frame_count:
#             if self.stop_thread:
#                 break
#
#             if self.is_can_read():
#                 # cv2
#                 # ret, frame = self.cur_cap[0].read()
#                 # if not ret:
#                 #     self.reset_cap()
#                 #     continue
#                 # self.frame_dict[self.cache_frame_ptr] = frame
#                 # self.cache_frame_ptr += 1
#                 self.batch_read_decord()
#
#             else:
#
#
#         self.end_time = time.time()
#         # print(f"读取耗时{self.end_time - self.start_time}")
#
#     def start_read_thread(self):
#         self.start_time = time.time()
#         for i in range(self.max_thread):
#             self.threads[i] = threading.Thread(target=self.read_frame)
#             self.threads[i].start()
#
#     def stop_read_thread(self):
#         self.stop_thread = True
#
#     def get_frame(self):
#         if self.get_frame_ptr == self.write_frame_count:
#             return None
#
#         frame_data = self.frame_dict.get(self.get_frame_ptr)
#         if frame_data is None:
#             if self.stop_thread:
#                 return None
#
#             MyLog.info("等待读图", self.get_frame_ptr)
#             time.sleep(1)
#             return self.get_frame()
#         else:
#             self.frame_dict[self.get_frame_ptr] = None
#             self.get_frame_ptr += 1
#             return frame_data
#
#
#
#
#
#     def __del__(self):
#         pass
#         # cv2
#         # for cap_data in self.caps:
#         #     cap_data[0].release()
#         #
#         # self.caps = []
#
#
# # faulthandler.enable()
# #
# # if __name__ == "__main__":
# #     # 创建应用程序实例
# #     app = QApplication(sys.argv)
# #
# #     def exception_hook(exctype, value, tb):
# #         print(f"Unhandled exception: {exctype.__name__}: {value}")
# #         print("Traceback (most recent call last):")
# #         traceback.print_tb(tb)  # 打印调用堆栈
# #
# #     sys.excepthook = exception_hook
# #
# #     paths = ["C:\\Users\\Administrator\\Desktop\\ceshi1.mp4",
# #             # "C:\\Users\\Administrator\\Desktop\\ceshihv.mp4",
# #              # "C:\\Users\\Administrator\\Desktop\\ceshi1.mp4",
# #              # "C:\\Users\\Administrator\\Desktop\\ceshi5.mp4"
# #             ]
# #
# #     GlobalData().video_paths = paths
# #
# #     frame_count = 30 * 10
# #
# #     rf = ReadFrame(paths, frame_count)
# #     rf.start_read_thread()
# #
# #     w, h = get_frame_size(paths[0])
# #     adjus_w, adjus_h = GlobalData().get_adjust_resolustion(w, h)
# #
# #     off_sr = OffScreenRender(rf, adjus_w, adjus_h, frame_count)
# #     off_sr.start_render_thread()
# #
# #     vw = VideoWrite(off_sr, adjus_w, adjus_h, frame_count)
# #     vw.start_write_thread()
# #
# #     # 启动事件循环
# #     sys.exit(app.exec())
