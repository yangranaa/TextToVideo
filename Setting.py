import ctypes
import json
import os
import sys

from FileTool import get_exe_dir

os.chdir(get_exe_dir())

class Setting:
    _setting = {}

    @classmethod
    def reload_setting(cls):
        with open('setting.json', 'r', encoding='utf-8') as json_file:
            cls._setting = json.load(json_file)

    @classmethod
    def get(cls, key):
        return cls._setting.get(key)

    @classmethod
    def set(cls, key, value):
        cls._setting[key] = value

Setting.reload_setting()

def hide_console():
    if sys.platform == 'win32':
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        # 获取当前控制台窗口句柄
        hwnd = kernel32.GetConsoleWindow()
        if hwnd != 0:
            # 隐藏窗口
            user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0

def init_console():
    if Setting.get('debug'):
        import faulthandler
        faulthandler.enable()
    else:
        hide_console()

init_console()

