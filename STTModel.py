import re
import threading
import time

import librosa
import cn2an
from pypinyin import pinyin, Style
from vosk import Model, KaldiRecognizer
import numpy as np
import json
from Levenshtein import ratio as levenshtein_ratio

from FileTool import get_all_files

class STTModel:

    _model = None
    _load_thread = None

    @classmethod
    def release(cls):
        if cls._model:
            cls._model = None

    @classmethod
    def load_model(cls):
        if cls._load_thread:
            cls._load_thread.join()
            cls._load_thread = None

        if not cls._model:
            cls._model = Model("vosk-model-cn-0.22")

    @classmethod
    def load_model_in_thread(cls):
        if cls._load_thread:
            cls._load_thread.join()
            cls._load_thread = None
            return

        if cls._model:
            return

        def load_model():
            cls._model = Model("vosk-model-cn-0.22")

        cls._load_thread = threading.Thread(target=load_model)
        cls._load_thread.start()

    @classmethod
    def text_to_pinyin(cls, text):
        """将中文文本转换为无调拼音字符串"""

        result = ' '

        pattern_str = r'[a-zA-Z]'
        pattern = re.compile(pattern_str)

        for item in pinyin(text, style=Style.NORMAL):
            letter_list = pattern.findall(item[0])
            word = ''.join(letter_list)
            if len(word) > 0:
                result += f' {word}'

        return result

    @classmethod
    def audio_to_text(cls, audio_path):

        # 用librosa读取音频（自动重采样+单声道）
        audio, sr = librosa.load(audio_path,
                                 sr=16000,  # 强制采样率
                                 mono=True,  # 单声道转换
                                 duration=60)  # 限制最长60秒

        # 转换音频格式为Vosk需要的int16
        audio_int = (audio * np.iinfo(np.int16).max).astype(np.int16)

        # 创建识别器
        rec = KaldiRecognizer(cls._model, 16000)

        # rec.AcceptWaveform(audio_int.tobytes())

        # 分块处理提高效率（500ms/块）
        block_size = 8000  # 16000Hz * 0.5s
        for i in range(0, len(audio_int), block_size):
            block = audio_int[i:i + block_size].tobytes()
            rec.AcceptWaveform(block)

        # 获取识别结果
        result = json.loads(rec.FinalResult())['text']
        result = ''.join(result)

        return result

    @classmethod
    def compare_similarity(cls, text_py, audio_py):
        """优化后的相似度比对"""
        # text_py = cls.text_to_pinyin(text)
        # audio_py = cls.text_to_pinyin(audio_text)

        ratio = levenshtein_ratio(text_py, audio_py)

        # 使用编辑距离相似度算法
        return ratio