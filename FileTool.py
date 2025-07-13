import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import winreg
from collections import OrderedDict
from pathlib import Path

import requests


def get_file_by_meipass(rela_path):
    """ 获取打包后资源的绝对路径 """
    if hasattr(sys, '_MEIPASS'):
        # 打包后的临时解压目录
        base_path = sys._MEIPASS
    else:
        # 开发环境的当前目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rela_path)

def get_file_by_exe_dir(rela_path):
    return os.path.join(get_exe_dir(), rela_path)


def get_exe_dir():
    """ 获取 EXE 所在目录（无论是否打包） """
    if getattr(sys, 'frozen', False):
        # 打包后的 EXE 路径：sys.executable 是 EXE 的绝对路径
        exe_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境：使用当前脚本的目录
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    return exe_dir

def get_appdata_directory():
    appdata_dir = os.getenv('APPDATA')
    return appdata_dir

def get_local_appdata_directory():
    # 获取当前用户的 Local AppData 目录
    local_appdata_dir = os.getenv('LOCALAPPDATA')
    return local_appdata_dir

def add_sys_path(path):
    if path not in sys.path:
        sys.path.append(path)

def get_increment_dir(dir, dir_name, make_dir=True):
    count = 1
    out_dir = f'{dir}/{dir_name}_{count}'
    while os.path.isdir(out_dir):
        count += 1
        out_dir = f'{dir}/{dir_name}_{count}'

    if make_dir:
        os.makedirs(out_dir)

    return out_dir

def get_increment_file_name(file_path):
    count = 0
    out_path = file_path
    filename, extension = os.path.splitext(out_path)
    while os.path.isfile(out_path):
        # 分离文件名和扩展名
        count += 1
        out_path = f'{filename}_{count}{extension}'

    return out_path

def copy_files_to_folder(src_folder, dst_folder):
    # 确保目标文件夹存在，如果不存在则创建
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    # 遍历源文件夹中的所有文件和子文件夹
    for item in os.listdir(src_folder):
        src_item = os.path.join(src_folder, item)  # 源文件或文件夹的完整路径
        dst_item = os.path.join(dst_folder, item)  # 目标文件或文件夹的完整路径

        # 如果是文件，则复制文件
        if os.path.isfile(src_item):
            shutil.copy2(src_item, dst_item)  # copy2 会保留元数据
        # 如果是文件夹，则递归调用该函数
        elif os.path.isdir(src_item):
            copy_files_to_folder(src_item, dst_item)


def delete_files_in_folder(folder_path):
    """
        删除指定目录下的所有文件和子目录，但保留目录本身。
        """
    if not os.path.exists(folder_path):
        # print(f"目录 {folder_path} 不存在。")
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
            # print(f"已删除文件: {item_path}")
        elif os.path.isdir(item_path):
            # 使用 shutil.rmtree 删除子目录及其内容
            shutil.rmtree(item_path)
            # print(f"已删除目录及内容: {item_path}")


def rename_file(file_path, new_name):

    """
    重命名文件
    :param file_path: 原文件的完整路径
    :param new_name: 新文件名（不包含路径）
    """
    # 获取文件所在的目录
    directory = os.path.dirname(file_path)

    # 获取文件的扩展名
    _, extension = os.path.splitext(file_path)

    # 构造新文件的完整路径
    new_file_path = os.path.join(directory, new_name + extension)
    # 重命名文件
    os.rename(file_path, new_file_path)


def is_file(file_path):
    return os.path.isfile(file_path)

def delete_file(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)

def sort_dir_by_modify_time(folder_path):
    # 列出路径下的所有内容
    all_items = os.listdir(folder_path)
    # 筛选出文件夹
    all_dirs = [os.path.join(folder_path, item) for item in all_items if os.path.isdir(os.path.join(folder_path, item))]

    def get_mtime(path):
        return os.path.getmtime(path)

    all_dirs.sort(key=get_mtime)

    return all_dirs

def get_all_files(folder_path, ext=None):
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            need_add = True
            if ext and not file.endswith(ext):
                need_add = False

            if need_add:
                file_path = os.path.join(root, file)
                all_files.append(file_path)

    return all_files

def sort_files_by_modify_time(folder_path):
    all_files = get_all_files(folder_path)

    def get_mtime(path):
        return os.path.getmtime(path)

    all_files.sort(key=get_mtime)

    return all_files

def sort_files_by_idx(folder_path, split_mark='_', ext='wav'):
    all_files = get_all_files(folder_path, ext)

    # # 定义正则表达式，匹配开头的数字部分
    # pattern = re.compile(r'^\d+')

    def get_idx(path):
        # file_name = Path(path).stem
        # match = pattern.match(file_name)
        # extracted_numbers = int(match.group())
        name_split = path.split(split_mark)
        idx = int(name_split[-1].split('.')[0])
        return idx

    all_files.sort(key=get_idx)

    return all_files

def calculate_string_hash(data, algorithm="sha256"):
    # 选择哈希算法
    hash_func = hashlib.new(algorithm)
    # 将字符串编码为字节流
    hash_func.update(data.encode('utf-8'))
    # 返回十六进制哈希值
    return hash_func.hexdigest()


def open_folder(path):
    """
    打开指定路径的文件夹（支持 Windows、macOS、Linux）
    参数：
        path: 要打开的文件夹路径（支持绝对路径或相对路径）
    """

    # 规范路径格式（确保路径存在）
    normalized_path = os.path.abspath(path)

    if not os.path.isdir(normalized_path):
        raise FileNotFoundError(f"文件夹不存在: {normalized_path}")

    # 根据操作系统执行不同命令
    system = platform.system()
    if system == "Windows":
        os.startfile(normalized_path)  # Windows 原生方法
    elif system == "Darwin":
        subprocess.run(["open", normalized_path], check=True)  # macOS
    else:
        subprocess.run(["xdg-open", normalized_path], check=True)  # Linux

    # print(f"已打开文件夹: {normalized_path}")
    return True

def save_json_file(path, data):
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as json_file:
        return json.load(json_file)

def download_url(url, save_path):
    try:
        # 创建保存目录（如果不存在）
        # os.makedirs(save_dir, exist_ok=True)

        # 从 URL 中提取文件名（自动去除查询参数）
        # path = urlsplit(url).path
        # filename = os.path.basename(path) or "default.jpg"
        # save_path = os.path.join(save_dir, filename)


        # 发送请求并保存
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        # print(f"下载成功：{save_path}")

        return save_path
    except Exception as e:
        # print(f"下载失败（{url}）：{str(e)}")
        return None


class SoftManager:
    _software_list = None

    @classmethod
    def get_installed_software(cls):
        software_list = OrderedDict()
        registry_paths = [
            # 64位系统上的64位软件
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            # 64位系统上的32位软件
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            # 当前用户安装的软件
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
        ]

        # 检查的安装路径键名（按优先级排序）
        install_path_keys = [
            'InstallLocation',  # 标准安装路径
            'InstallDir',  # 替代安装路径
            'InstallPath',  # 另一种可能路径
            'UninstallString',  # 有时包含路径
            'DisplayIcon'  # 图标路径可能包含目录
        ]

        for root, path in registry_paths:
            try:
                with winreg.OpenKey(root, path) as key:
                    index = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, index)
                            subkey_path = f"{path}\\{subkey_name}"
                            with winreg.OpenKey(root, subkey_path) as subkey:
                                try:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]

                                    # 跳过无效条目
                                    if not name or name in software_list:
                                        continue

                                    # 获取安装路径
                                    install_path = ""
                                    for path_key in install_path_keys:
                                        try:
                                            val = winreg.QueryValueEx(subkey, path_key)[0]
                                            if val:
                                                # 处理路径中的双引号和结尾的反斜杠
                                                clean_val = val.strip('"')
                                                if '\\' in clean_val:
                                                    install_path = clean_val
                                                    # 如果是文件路径，提取目录部分
                                                    if '.' in clean_val.split('\\')[-1]:
                                                        install_path = '\\'.join(clean_val.split('\\')[:-1])
                                                    break
                                        except FileNotFoundError:
                                            continue

                                    # 补充信息
                                    try:
                                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                    except FileNotFoundError:
                                        version = "N/A"

                                    software_list[name] = {
                                        'version': version,
                                        'install_path': install_path.replace('\\\\', '\\') if install_path else "Not Found",
                                        'registry_path': f"{root}\\{subkey_path}"
                                    }
                                except FileNotFoundError:
                                    pass
                        except OSError:
                            break
                        index += 1
            except FileNotFoundError:
                continue

        return software_list

    @classmethod
    def get_soft_by_name(cls, name):
        if cls._software_list is None:
            cls._software_list = cls.get_installed_software()

        return cls._software_list.get(name)

#-------------------------------------------------------------------------------------------------------

import win32com.client
import pythoncom


def drag_drop_files(hwnd, file_paths):
    # 初始化 COM
    try:
        pythoncom.CoInitialize()
        print("COM环境已成功初始化")
    except Exception as e:
        print(f"COM环境初始化失败: {e}")

    # 创建数据对象
    data_obj = win32com.client.Dispatch(f'{pythoncom.IID_IDataObject}')

    # 设置文件列表
    file_group = win32com.client.Dispatch("FileGroupDescriptor")
    for path in file_paths:
        file_group.Files.Add()
        file_group.Files[-1].FileName = path.split("\\")[-1]  # 文件名
        file_group.Files[-1].Path = path  # 完整路径
    data_obj.SetData(file_group)

    # 获取目标窗口的 IDropTarget 接口
    drop_target = win32com.client.Dispatch(pythoncom.IID_IDropTarget)
    drop_target.hwnd = hwnd

    # 执行拖放
    effect = win32com.client.constants.DROPEFFECT_COPY
    drop_target.Drop(data_obj, 0, (100, 100), effect)

    # 清理 COM
    pythoncom.CoUninitialize()

#-------------------------------------------------------------------
# import base64
#
# path = "E:\\JianyingPro Drafts\\3月12日 (1)\\.backup\\20250312145616_04fe3b308bd38e0d2caacb0c15693d94.save.bak"
#
# text = ""
#
# with open(path, "r", encoding='utf-8') as file:
#     data = file.read()
#     text = base64.b64decode(data)
#
#     # text = base64.b64decode(decoded_file_data)
#     # text = decoded_file_data.decode('latin-1')
#     print(text)


# byte_data = b"\x8c"
# decoded_string = byte_data.decode('latin-1')  # 使用 latin-1 编码解码
# print(decoded_string)  # 输出：

# 如果是二进制文件内容，可以保存到文件
# with open("decoded_file.bin", "wb") as file:
#     file.write(text)


# windows = pygetwindow.getWindowsWithTitle('hhhh')
# windows[0].activate()
# drag_drop_files(windows[0]._hWnd, ["音频字幕.srt"])
# print('result')