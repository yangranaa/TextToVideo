import os
import threading
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from AudioTool import connect_voice_clips, variation_audio
from FileTool import delete_files_in_folder, copy_files_to_folder, get_all_files, rename_file
from GlobalData import GlobalData
from STTModel import STTModel

class QtSignals(QObject):
    """定义信号的类"""
    finished = pyqtSignal(dict)

class AudioOpThread:

    def __init__(self, jian_ying_clip_path=None):
        self.signals = QtSignals()
        self.jian_ying_clip_path = jian_ying_clip_path

    def rename_jianying_voice(self, clips_path, text_list):
        all_file = get_all_files(clips_path)
        if len(all_file) != len(text_list):
            raise RuntimeError(f"文本与配音文件不符。{len(all_file)},{len(text_list)}")

        self.signals.finished.emit({"value": 1, "total_value": 2, 'loading': True})
        STTModel.load_model()

        texts_data = {}
        for idx, text in enumerate(text_list):
            texts_data[idx] = {}
            texts_data[idx]['py'] = STTModel.text_to_pinyin(text)
            texts_data[idx]['text'] = text

        clips_data = {}
        for idx, file in enumerate(all_file):
            text = STTModel.audio_to_text(file)
            py_audio = STTModel.text_to_pinyin(text)
            clips_data[file] = py_audio
            self.signals.finished.emit({"value": idx, "total_value": len(all_file), 'rename':True})

        no_math_clip = clips_data.copy()
        zero_ratio_clip = {}

        def math_text_file(file, datas):
            file_py = clips_data[file]

            max_ratio = 0
            math_idx = None
            for idx, text_data in datas.items():
                ratio = STTModel.compare_similarity(text_data['py'], file_py)

                if max_ratio < ratio:
                    if text_data.get('file_py') == file_py:
                        continue
                    math_idx = idx
                    max_ratio = ratio

                if max_ratio >= 1:
                    break

            text_data = datas[math_idx]

            if text_data.get('ratio'):
                if text_data['ratio'] < max_ratio:
                    old_file = text_data['file']
                    no_math_clip[old_file] = text_data['file_py']

                    text_data['ratio'] = max_ratio
                    text_data['file'] = file
                    text_data['file_py'] = file_py

                    no_math_clip.pop(file)

                    math_text_file(old_file, datas)
            else:
                text_data['ratio'] = max_ratio
                text_data['file'] = file
                text_data['file_py'] = file_py

                no_math_clip.pop(file)

        while len(no_math_clip) > 0:
            datas = {}

            for idx, data in texts_data.items():
                if data.get('file') is None:
                    datas[idx] = data

            for file in [*no_math_clip.keys()]:
                math_text_file(file, datas)


        # def get_length_math(length, datas):
        #     min_step_len = 9999999
        #     math_file = None
        #     for file,py in no_math_clip.items():
        #         step_len = abs(len(py) - length)
        #         if step_len < min_step_len:
        #             min_step_len = step_len
        #             math_file = file
        #
        #     no_math_clip.pop(math_file)
        #
        #     return math_file

        # total = 0

        # for idx, data in texts_data.items():
        #     if data.get('file') is None:
        #         data['file'] = get_length_math(len(data['py']))
        #     else:
        #         total += data['ratio']
        #         print("匹配", data['py'], data['text'], data['ratio'], data['file_py'])
        #
        # print('ttttttttttttt', total)

        for idx, data in texts_data.items():
            if data['ratio'] < 0.7:
                print("匹配", data['text'], data['py'], data['ratio'], data['file_py'])

            rename_file(data['file'], f'{data['text']}_{idx}')

    def start_connect_voice_thread(self, source_path, sound_save_path, srt_save_path=None, text_list=None, **kwargs):
        kwargs['signal'] = self.signals

        GlobalData().save_data()

        def _fun():
            try:
                if self.jian_ying_clip_path:

                    if os.path.exists(source_path):
                        delete_files_in_folder(source_path)
                    else:
                        os.mkdir(source_path)

                    copy_files_to_folder(self.jian_ying_clip_path, source_path)

                    self.rename_jianying_voice(source_path, text_list)

                connect_voice_clips(source_path, sound_save_path, srt_save_path, text_list, **kwargs)
            except Exception as e:
                self.signals.finished.emit({'error': e.__str__()})



        thread = threading.Thread(target=_fun)
        thread.start()

    def start_variation_audio_thread(self, audio_path, out_path, **kwargs):
        kwargs['signal'] = self.signals

        GlobalData().save_data()

        def _fun():
            try:
                variation_audio(audio_path, out_path, **kwargs)
            except Exception as e:
                self.signals.finished.emit({'error': e.__str__()})

        thread = threading.Thread(target=_fun)
        thread.start()