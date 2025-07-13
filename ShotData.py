import ast
import math
import os
import random
import threading

from PyQt6.QtCore import QObject, pyqtSignal

from AgentManager import AgentManager
from ShotEffConfig import shot_eff_config, shot_enter_eff_config, shot_after_eff_config
from FileTool import save_json_file, load_json_file, get_all_files, get_increment_file_name, download_url
from GlobalData import GlobalData
from GlobalSignals import global_signals
from PresetWindow import PresetData
from VoiceText import voice_text_lines


class ShotData(QObject):

    show_red = True

    shot_datas = []

    data_change = pyqtSignal(dict)


    @classmethod
    def read_data_from_file(cls):
        shot_path = GlobalData().shot_path
        cls.shot_datas.clear()

        if os.path.isfile(shot_path):
            datas = load_json_file(shot_path)

            for data in datas:
                shot_data = ShotData(data)
                cls.shot_datas.append(shot_data)

    @classmethod
    def gen_shot_datas_by_data(cls, data):
        cls.shot_datas.clear()

        shot_list = ast.literal_eval(data)

        replace_dic = {"血":"红"}

        for shot in shot_list:
            promt = shot[1]

            for src, dst in replace_dic.items():
                promt = promt.replace(src, dst)

            shot_data = ShotData()
            shot_data.line_list = shot[0]
            shot_data.promt = promt

            cls.shot_datas.append(shot_data)

        cls.save_data()

        global_signals.reset_shot_data.emit()


    @classmethod
    def gen_shot_datas(cls, img_dir):
        cls.shot_datas.clear()

        img_paths = get_all_files(img_dir, 'jpg')

        text_lines = voice_text_lines.line_list
        max_line = len(text_lines) - 1
        shot_line_num = math.ceil(len(text_lines) / len(img_paths))

        for idx, img_path in enumerate(img_paths):
            line_start_idx = min(shot_line_num * idx, max_line)
            line_end_idx = min((idx + 1) * shot_line_num, max_line + 1)
            text_line = []
            for id in range(line_start_idx, line_end_idx):
                text_line.append(text_lines[id])

            shot_data = ShotData()
            shot_data.line_list = text_line
            shot_data.img_path = img_path
            cls.shot_datas.append(shot_data)

        cls.save_data()

    @classmethod
    def gen_first_data(cls):
        cls.shot_datas.clear()

        shot_data = ShotData([None, voice_text_lines.line_list, shot_eff_config[0][1], ''])
        cls.shot_datas.append(shot_data)

        cls.save_data()


    @classmethod
    def insert_data(cls, idx, data_list):

        shot_data = ShotData(data_list)
        cls.shot_datas.insert(idx, shot_data)
        cls.save_data()

        return shot_data

    @classmethod
    def del_data(cls, idx):
        del_data = cls.shot_datas.pop(idx)

        if len(del_data.line_list) > 0:
            insert_data = cls.get_data(idx - 1)
            if insert_data is not None:
                for line in del_data.line_list:
                    insert_data.insert_line(line, False)
            else:
                next_data = cls.get_data(idx)
                if next_data is not None:
                    del_data.line_list.reverse()
                    for line in del_data.line_list:
                        next_data.insert_line(line, True)

        cls.save_data()

    @classmethod
    def move_shot_text(cls, idx, is_up):
        shot_data = cls.get_data(idx)
        if shot_data is None:
            return

        if is_up:
            insert_data = cls.get_data(idx - 1)
        else:
            insert_data = cls.get_data(idx + 1)

        if insert_data is not None:
            line = shot_data.pop_line(is_up)

            if line is None:
                return

            insert_data.insert_line(line, not is_up)

        cls.save_data()

    @classmethod
    def save_data(cls):
        shot_path = GlobalData().shot_path
        datas = [shot_data.to_array() for shot_data in cls.shot_datas]
        save_json_file(shot_path, datas)

    @classmethod
    def get_data(cls, idx):
        if len(cls.shot_datas) > idx >= 0:
            return cls.shot_datas[idx]
        else:
            return None


    # data [img_path, text, eff]
    def __init__(self, data_list=None):
        super().__init__()

        if data_list is None:
            enter_config = random.choice(shot_enter_eff_config)
            after_config = shot_after_eff_config[random.randint(0,1)] #random.choice(shot_after_eff_config)
            data_list = [None, [], shot_eff_config[0][1], None, True, [], enter_config[1], after_config[1]]

        if len(data_list) < 8:
            data_list.insert(4, True)
            data_list.insert(5, [])
            data_list.insert(6, shot_enter_eff_config[0][1])
            data_list.insert(7, shot_after_eff_config[0][1])


        self.img_path = data_list[0]
        self.line_list = data_list[1]
        self.eff = data_list[2]
        self.promt = data_list[3]
        self.red = data_list[4]
        self.backup_imgs = data_list[5]
        self.enter_eff = data_list[6]
        self.after_eff = data_list[7]

        self.req_thread = None
        self.req_err = None

    def req_pic(self):
        self.red = True

        if self.promt:
            promt = self.promt
        else:
            return

        for name, value in PresetData.preset_dic.items():
            if name != 'style':
                promt = promt.replace(name, f"{value}")

        promt = PresetData.preset_dic['style'] + promt

        self.req_err = None

        def req_fun():
            url_list = AgentManager.req_gen_pic(promt)

            success = False

            if not os.path.exists(GlobalData().imgs_path):
                os.mkdir(GlobalData().imgs_path)

            for url in url_list:
                save_path = get_increment_file_name(f'{GlobalData().imgs_path}/{id(url)}{self.promt}.jpg')

                result = download_url(url, save_path)

                if result:
                    self.backup_imgs.insert(0, save_path)

                    success = True

            if success:
                self.img_path = self.backup_imgs[0]
            else:
                self.req_err = '生图失败'

            self.req_thread = None
            self.save_data()
            self.emit_data_changed()

        self.req_thread = threading.Thread(target=req_fun)
        self.req_thread.start()


    def insert_line(self, line, is_top):
        if is_top:
            self.line_list.insert(0, line)
        else:
            self.line_list.append(line)

        self.emit_data_changed()

    def pop_line(self, is_top):
        result = None
        if len(self.line_list) > 0:
            if is_top:
                result = self.line_list.pop(0)
            else:
                result = self.line_list.pop()

            self.emit_data_changed()

        return result

    def emit_data_changed(self):
        self.data_change.emit({'data_change':True})

    def to_array(self):
        return [self.img_path, self.line_list, self.eff, self.promt, self.red, self.backup_imgs, self.enter_eff, self.after_eff]