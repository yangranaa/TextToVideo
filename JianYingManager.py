
import os
import subprocess
import time
from datetime import date

import psutil
import pygetwindow
import pyperclip
from PyQt6.QtCore import QThread, pyqtSignal

from FileTool import get_local_appdata_directory, sort_dir_by_modify_time, SoftManager, get_file_by_exe_dir
import pyautogui
import pyscreeze

from GlobalData import GlobalData

pyautogui.MINIMUM_DURATION = 0.2
pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = False
screen_width, screen_height = pyautogui.size()

class JianYingManager:

    _app_setting = None
    jian_ying_path = None
    jian_ying_draft_path = None
    draft_open_time = None
    last_draft_dir = None
    home_handle = None

    jmi = 'jianying_math_img/'

    @classmethod
    def read_jian_ying_config(cls):
        config_path = get_local_appdata_directory() + '/JianyingPro/User Data/Config/globalSetting'
        if cls._app_setting:
            return

        cls._app_setting = {}
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                setting = line.split('=')
                if len(setting) > 1 and setting[0] == 'currentCustomDraftPath':
                    cls._app_setting[setting[0]] = setting[1]

    @classmethod
    def get_last_draft_path(cls):
        if cls._app_setting is None:
            cls.read_jian_ying_config()

        draft_dir = cls._app_setting.get('currentCustomDraftPath')
        if draft_dir:
            files = sort_dir_by_modify_time(draft_dir)
            files.reverse()

            today = date.today()
            for file in files:
                if os.path.getmtime(file) > cls.draft_open_time:
                    data_str = f'{today.month}月{today.day}日'
                    if data_str in file:
                        cls.last_draft_dir = os.path.abspath(file)
                        return cls.last_draft_dir

        return None

    @classmethod
    def get_jian_ying_app_path(cls):
        if cls.jian_ying_path:
            return cls.jian_ying_path

        soft_data = SoftManager.get_soft_by_name('剪映专业版')
        if soft_data:
            path = soft_data['install_path'] + '/JianyingPro.exe'
            cls.jian_ying_path = path
            return path

    @classmethod
    def terminate_jian_ying(cls):
        # 遍历所有进程
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == "JianyingPro.exe":
                    proc.terminate()
                    proc.wait(3)
            except psutil.NoSuchProcess:
                print(f"进程 {proc.info['process_name']} 在终止前已结束。")
            except psutil.TimeoutExpired:
                # 如果超时仍未结束，强制杀死进程
                print(f"进程 {proc.info['process_name']} 被强制杀死。")
            except Exception as e:
                print(f"终止进程 {proc.info['process_name']} 时出现错误: {e}")

    @classmethod
    def run_jian_ying_program(cls):
        cls.terminate_jian_ying()
        subprocess.Popen(cls.jian_ying_path, shell=True)

    @classmethod
    def wait_window_with_title(cls, title, step_time=0.1, try_times=100, exc_fun=None, match_fun=None):
        windows = pygetwindow.getWindowsWithTitle(title)
        window = None
        if len(windows) > 0:
            window = windows[0] if match_fun is None else match_fun(windows)
        while not window:
            if try_times:
                try_times -= 1
                if try_times < 1:
                    return
            if exc_fun:
                exc_fun()
            windows = pygetwindow.getWindowsWithTitle(title)
            if len(windows) > 0:
                window = windows[0] if match_fun is None else match_fun(windows)
            time.sleep(step_time)

        return window

    @classmethod
    def wait_find_pos(cls, img_str, rect, window, step_time=0.1, try_times=50, exc_fun=None):
        window.activate()

        img_str = get_file_by_exe_dir(cls.jmi + img_str)

        find_pos = pyautogui.locateOnScreen(img_str, region=rect)
        while not find_pos:
            if try_times:
                try_times -= 1
                if try_times < 1:
                    return
            if exc_fun:
                exc_fun()
            find_pos = pyautogui.locateOnScreen(img_str, region=rect)
            time.sleep(step_time)

        return find_pos

    @classmethod
    def minimize_draft_window(cls):
        cls.draft_window.minimize()

    @classmethod
    def repose_draft_window(cls):
        cls.draft_window.restore()
        cls.draft_window.activate()
        cls.draft_window.top = 10
        cls.draft_window.left = 10
        cls.draft_window.width = 1180
        cls.draft_window.height = 720

    @classmethod
    def repose_home_page(cls):
        cls.home_page.activate()
        cls.home_page.left = 10
        cls.home_page.top = 10
        cls.home_page.width = 980
        cls.home_page.height = 650

    @classmethod
    def wait_draft_window(cls):

        def match_draft(windows):
            for window in windows:
                if window._hWnd != cls.home_handle:
                    return window

        # 等待打开草稿
        cls.draft_window = cls.wait_window_with_title("剪映专业版", match_fun=match_draft)
        if cls.draft_window:
            cls.repose_draft_window()
        else:
            raise RuntimeError("无法自动打开草稿，请改用手动操作生成配音片段。")

        while not cls.draft_window.isActive:
            cls.draft_window.activate()

    @classmethod
    def reset_draft_layout(cls):
        cls.wait_draft_window()
        cls.repose_draft_window()

        def match_layout(windows):
            for window in windows:
                if window.width == screen_width:
                    return window

        search_rect = None#(714, 18, 250, 26)
        buju_pos = cls.wait_find_pos("buju.png", search_rect, cls.draft_window)

        if not buju_pos:
            raise RuntimeError("无法定位布局按钮，请改用手动操作生成配音片段。")

        pyautogui.click(buju_pos.left + 10, buju_pos.top + 5)
        layout_menu = cls.wait_window_with_title("JianyingPro", match_fun=match_layout)

        if not layout_menu:
            raise RuntimeError("无法打开布局菜单，请改用手动操作生成配音片段。")

        pyautogui.click(buju_pos.left + 10, buju_pos.top + 40)

        while layout_menu.isActive:
            pyautogui.click(buju_pos.left + 10, buju_pos.top + 40)

        cls.repose_draft_window()
        pyautogui.click(buju_pos.left + 10, buju_pos.top + 5)
        layout_menu = cls.wait_window_with_title("JianyingPro", match_fun=match_layout)

        if not layout_menu:
            raise RuntimeError("无法打开布局菜单，请改用手动操作生成配音片段。")

        while layout_menu.isActive:
            pyautogui.click(buju_pos.left + 10, buju_pos.top + 158)

    @classmethod
    def open_draft(cls):
        cls.get_jian_ying_app_path()
        cls.run_jian_ying_program()

        home_page_name = "剪映专业版"
        cls.home_page = cls.wait_window_with_title(home_page_name)
        if not cls.home_page:
            raise RuntimeError("无法开启剪映，请改用手动操作生成配音片段。")

        cls.repose_home_page()
        cls.home_handle = cls.home_page._hWnd

        kaishichuangzuo_pos = cls.wait_find_pos('kaishichuangzuo.png', None, cls.home_page)

        if kaishichuangzuo_pos:
            cls.home_page.activate()
            cls.draft_open_time = time.time()
            pyautogui.click(kaishichuangzuo_pos.left, kaishichuangzuo_pos.top)
        else:
            raise RuntimeError("找不到剪映创作按钮，请改用手动操作生成配音片段。")

        cls.wait_draft_window()

    @classmethod
    def input_srt(cls, srt_path):
        cls.repose_draft_window()
        search_rect = None#(337, 45, 30, 30)
        zimu_pos = cls.wait_find_pos('zimu.png', search_rect, cls.draft_window, try_times=50)

        if not zimu_pos:
            raise RuntimeError("匹配不到字幕位置，请改用手动操作生成配音片段。")

        pyperclip.copy(srt_path)
        pyautogui.hotkey('ctrl', 'i')
        input_window = cls.wait_window_with_title('请选择媒体资源')
        if not input_window:
            raise RuntimeError("获取不到媒体导入框，请改用手动操作生成配音片段。")

        input_window.activate()
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)
        input_window.activate()

        cls.try_count = 0

        while input_window.visible:
            pyautogui.hotkey('enter')
            cls.try_count += 1
            if cls.try_count > 10:
                raise RuntimeError("无法输入文件，请改用手动操作生成配音片段。")
            time.sleep(0.1)

        def is_hint_window(windows):
            for window in windows:
                if window.width == 266:
                    return window

        hint_window = cls.wait_window_with_title("JianyingPro", match_fun=is_hint_window)

        if not hint_window:
            raise RuntimeError("获取不到提示窗，请改用手动操作生成配音片段。")

        cls.repose_draft_window()
        pyautogui.click(zimu_pos.left + 10, zimu_pos.top + 10)

        search_rect = None#(31, 264, 55, 22)
        xinjianzimu_pos = cls.wait_find_pos('xinjianzimu.png', search_rect, cls.draft_window, try_times=50)
        if xinjianzimu_pos:
            pyautogui.click(xinjianzimu_pos.left + 20, xinjianzimu_pos.top + 10)
        else:
            raise RuntimeError("获取不到新建字幕按钮，请改用手动操作生成配音片段。")

    @classmethod
    def add_srt_time_line(cls):
        cls.repose_draft_window()
        tubiao_rect = None#(142, 151, 80, 80)
        zimutubiao_pos = cls.wait_find_pos("zimutubiao.png", tubiao_rect, cls.draft_window)
        if not zimutubiao_pos:
            raise RuntimeError("找不到srt图标，请改用手动操作生成配音片段。")

        pyautogui.moveTo(zimutubiao_pos.left + 20, zimutubiao_pos.top + 20)
        pyautogui.moveTo(zimutubiao_pos.left + 25, zimutubiao_pos.top + 20, duration=0.1)
        jiahao_pos = cls.wait_find_pos("jiahao.png", None, window=cls.draft_window)
        if jiahao_pos:
            pyautogui.click(jiahao_pos.left + 10, jiahao_pos.top)
        else:
            raise RuntimeError("找不到srt添加按钮，请改用手动操作生成配音片段。")

        def is_hint_window(windows):
            for window in windows:
                if window.width == 186:
                    return window

        hint_window = cls.wait_window_with_title("JianyingPro", match_fun=is_hint_window)
        if not hint_window:
            raise RuntimeError("找不到提示窗口，请改用手动操作生成配音片段。")
        while hint_window.visible:
            pass

    @classmethod
    def req_voice(cls):
        cls.wait_draft_window()
        pyautogui.click(1156, 540)
        pyautogui.hotkey('ctrl','a')
        langdu_pos = cls.wait_find_pos("langdu.png", None, window=cls.draft_window)
        if not langdu_pos:
            raise RuntimeError("找不到朗读选项，请改用手动操作生成配音片段。")
        pyautogui.click(langdu_pos.left + 5, langdu_pos.top + 5)

        shoucang_pos = cls.wait_find_pos("shoucang.png", None, window=cls.draft_window)
        if not shoucang_pos:
            raise RuntimeError("找不到收藏选项，请改用手动操作生成配音片段。")
        pyautogui.click(shoucang_pos.left + 10, shoucang_pos.top + 5)

        shoucangbiaoqian_pos = cls.wait_find_pos("shoucangbiaoqian.png", None, window=cls.draft_window, try_times=10)
        try_count = 0
        if not shoucangbiaoqian_pos and try_count < 5:
            try_count += 1
            pyautogui.click(shoucang_pos.left + 10, shoucang_pos.top + 5)
            shoucangbiaoqian_pos = cls.wait_find_pos("shoucangbiaoqian.png", None, window=cls.draft_window,
                                                     try_times=10)

        if not shoucangbiaoqian_pos:
            raise RuntimeError("找不到收藏标签，请改用手动操作生成配音片段。")

        pyautogui.moveTo(shoucangbiaoqian_pos.left + 32, shoucangbiaoqian_pos.top + 53)
        huangxing_pos = cls.wait_find_pos("huangxing.png", None, window=cls.draft_window, try_times=10)

        try_count = 0
        while not huangxing_pos and try_count < 5:
            try_count += 1
            cls.repose_draft_window()
            pyautogui.click(shoucang_pos.left + 10, shoucang_pos.top + 5)
            pyautogui.moveTo(shoucangbiaoqian_pos.left + 32, shoucangbiaoqian_pos.top + 53)
            huangxing_pos = cls.wait_find_pos("huangxing.png", None, window=cls.draft_window, try_times=10)

        if not huangxing_pos:
            raise RuntimeError("识别不到位置，请改用手动操作生成配音片段。")

        pyautogui.click(shoucangbiaoqian_pos.left + 32, shoucangbiaoqian_pos.top + 53)
        tiaosu_pos = cls.wait_find_pos("tiaosu.png", None, window=cls.draft_window)
        if not tiaosu_pos:
            raise RuntimeError("识别不到位置，请改用手动操作生成配音片段。")
        pyautogui.click(tiaosu_pos.left + 5, tiaosu_pos.top + 5)

        def is_sudu_window(windows):
            for window in windows:
                if window.height == 744 or window.height == 706:
                    return window

        sudu_window = cls.wait_window_with_title("JianyingPro", match_fun=is_sudu_window)

        if not sudu_window:
            raise RuntimeError("打不开调速界面，请改用手动操作生成配音片段。")

        sudu_pos = cls.wait_find_pos("sudu.png", None, window=sudu_window)
        pyautogui.click(sudu_pos.left - 25, sudu_pos.top + 6)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.write(f'{GlobalData().voice_speed:.2f}')

        kaishilangdu_pos = cls.wait_find_pos("kaishilangdu.png", None, window=cls.draft_window)
        if not kaishilangdu_pos:
            raise RuntimeError("找不到开始朗读按钮，请改用手动操作生成配音片段。")

        pyautogui.click(kaishilangdu_pos.left + 20, kaishilangdu_pos.top + 12, 2, 0.1)

        def is_read_window(windows):
            for window in windows:
                if window.width == 168:
                    return window

        read_window = JianYingManager.wait_window_with_title("JianyingPro", match_fun=is_read_window)
        if not read_window:
            raise RuntimeError("找不到开始朗读按钮，请改用手动操作生成配音片段。")

        while read_window.visible == 1 and (read_window.title == 'JianyingPro'):
            # print('等待朗读完成', read_window.visible, read_window.title)
            pass

        return True

class JianYingOpThread(QThread):
    finished = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            JianYingManager.open_draft()
            JianYingManager.wait_draft_window()
            JianYingManager.reset_draft_layout()
            JianYingManager.input_srt(GlobalData().temp_srt_path)
            JianYingManager.add_srt_time_line()
            JianYingManager.req_voice()
            JianYingManager.terminate_jian_ying()
        except Exception as e:
            self.finished.emit({'error':e.__str__()})
            return

        self.finished.emit({'finish': True})

if __name__ == "__main__":
    jian = JianYingOpThread()
    jian.run()


    # print(os.path.abspath("temp.srt"))
    # windows = pygetwindow.getWindowsWithTitle("JianyingPro")
    # for window in windows:
    #     print(window)
    #
    # print(pygetwindow.getActiveWindow())

    # JianYingManager.wait_draft_window()
    # jiahao_pos = JianYingManager.wait_find_pos("jiahao.png", None, window=JianYingManager.draft_window)
    # if jiahao_pos:
    #     pyautogui.click(jiahao_pos.left + 10, jiahao_pos.top)
    # else:
    #     raise RuntimeError("找不到srt添加按钮，请改用手动操作生成配音片段。")

    # pyautogui.write(f'{164 * 0.01:.2f}')

    pass
#
#
#     pass
#
# # windows = pygetwindow.getWindowsWithTitle('请选择')
# # windows[0].activate()
# # print(windows[0]._hWnd, windows[0].title, windows[0], os.path.abspath("音频字幕.srt"))
