import torch

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, QThread
import soundfile as sf
import os

from FileTool import get_file_by_exe_dir

# 🇺🇸 'a' => American English, 🇬🇧 'b' => British English
# 🇯🇵 'j' => Japanese: pip install misaki[ja]
# 🇨🇳 'z' => Mandarin Chinese: pip install misaki[zh]

voice_models = {}
voice_models['Kokoro-82M-v1.1-zh'] = {'repo_id': 'hexgrad/Kokoro-82M-v1.1-zh', 'pth': 'data/kokoro-v1_1-zh.pth', 'voices_path': 'voices/kokoro-v1_1', 'config': 'data/config1_1.json'}
voice_models['Kokoro-82M-v1'] = {'repo_id': 'hexgrad/Kokoro-82M', 'pth': 'data/kokoro-v1_0.pth', 'voices_path': 'voices/kokoro-v1_0', 'config': 'data/config1_0.json'}

def init_voice_config():
    # 获取目录中的所有文件和文件夹
    voice_type = ['z','a']

    for model in voice_models.values():
        model['voices'] = {}

        voices_path = get_file_by_exe_dir(model['voices_path'])

        all_items = os.listdir(voices_path)
        # 筛选出文件
        files = [item for item in all_items if os.path.splitext(item)[1] == '.pt']

        for file in files:
            if file[0] in voice_type:
                if model['voices'].get(file[0]) is None:
                    model['voices'][file[0]] = []
            else:
                continue

            if file == 'zm_yunxi.pt':
                model['voices'][file[0]].insert(0, file)
            else:
                model['voices'][file[0]].append(file)

class GenVoiceSignals(QObject):
    """定义信号的类"""
    finished = pyqtSignal(dict)

class GenVoiceTask(QRunnable):

    def __init__(self, text, voice, speed, idx):
        super().__init__()
        self.text = text
        self.voice = voice
        self.speed = speed
        self.idx = idx
        self.signals = GenVoiceSignals()

    def run(self):
        gv = GenVoice()
        try:
            gv.gen_voice(self.text, self.voice, self.speed, self.idx)
        except Exception as e:
            self.signals.finished.emit({'sucess': False, 'msg': f'{e}'})
        else:
            self.signals.finished.emit({'sucess': True, 'idx':self.idx})

class InitPipelineThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, model_name):
        super().__init__()
        self.model_cfg = voice_models[model_name]
        self.model_name = model_name

    def run(self):
        repo_id = self.model_cfg['repo_id']
        con_json = get_file_by_exe_dir(self.model_cfg['config'])
        model_pth = get_file_by_exe_dir(self.model_cfg['pth'])

        from kokoro import KModel, KPipeline

        k_model = KModel(repo_id=repo_id, config=con_json, model=model_pth)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        k_model = k_model.to(device).eval()

        if GenVoice().pipelines.get(self.model_name) is None:
            GenVoice().pipelines[self.model_name] = {}

        GenVoice().pipelines[self.model_name]['a'] = KPipeline(repo_id=repo_id, lang_code='a', model=k_model)

        def en_callable(text):
            if text == 'Kokoro':
                return 'kˈOkəɹO'
            elif text == 'Sol':
                return 'sˈOl'

            en_pt_path = get_file_by_exe_dir('voices/kokoro-v1_1/af_sol.pt')
            return next(GenVoice().pipelines[self.model_name]['a'](text, voice=en_pt_path)).phonemes

        GenVoice().pipelines[self.model_name]['z'] = KPipeline(repo_id=repo_id, lang_code='z', model=k_model, en_callable=en_callable)

        # self.pipelines['j'] = KPipeline(repo_id=repo_id, lang_code='j', model=self.k_model,
        #                                  en_callable=en_callable)

        self.finished.emit(self.model_name)

class GenVoice:
    _instance = None  # 类属性，用于存储单例实例
    _initialized = False
    _save_path = ''

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.pipelines = {}
        self.load_model_thread = {}
        self._initialized = True
        self.sel_model_name = None
        self.load_cb = None

        init_voice_config()

    def release(self):
        for key in list(self.load_model_thread.keys()):
            load_thread = self.load_model_thread.pop(key)
            load_thread.quit()
            load_thread.wait()

        self.pipelines = {}

        if torch.cuda.is_available():
            torch.cuda.empty_cache()


    def select_model(self, model_name, load_cb=None):
        self.sel_model_name = model_name
        self.model_cfg = voice_models[self.sel_model_name]
        if self.load_model_thread.get(model_name) is None:
            self.load_model_thread[model_name] = InitPipelineThread(model_name)
            self.load_model_thread[model_name].finished.connect(load_cb)
            self.load_model_thread[model_name].start()

            return True

        return False

    def is_model_loading(self):
        if not self.pipelines.get(self.sel_model_name):
            return True
        return False

    def gen_voice(self, text, voice, total_speed, idx):
        pipeline = self.pipelines[self.sel_model_name][voice[0]]

        def speed_callable(len_ps):
            speed = 0.8
            if len_ps <= 83:
                speed = 1
            elif len_ps < 183:
                speed = 1 - (len_ps - 83) / 500
            return speed * 1#total_speed

        voice_path = get_file_by_exe_dir(f'{self.model_cfg['voices_path']}/{voice}')

        generator = pipeline(text, voice=voice_path, speed=speed_callable)
        f = f'{self._save_path}/{text}_{idx}.wav'
        result = next(generator)
        wav = result.audio
        sf.write(f, wav, 24000)