import base64
import hashlib
import json
import os
import re
import time

import requests
from PyQt6.QtCore import QThread, pyqtSignal, QRunnable, QObject


def encode_word(word, dict):
    html_str = '<root><speak isMain="true"'
    end_str = ''

    for key, value in dict.items():
        if key != 'emotion':
            html_str += f' {key}="{value}"'

    html_str += '>'

    if dict.get('emotion'):
        html_str += f'<emotion'
        for key, value in dict.get('emotion').items():
            html_str += f' {key}="{value}"'

        html_str += '>'
        end_str += '</emotion>'

    html_str += f'<s line="1">{word}</s>'

    html_str += end_str + '</speak></root>'
    # print('<root><speak isMain="true" name="云希Pro" voice="azure_zh-CN-YunxiNeural" hostType="6" volume="1" pitch="0" rate="1.4"><emotion category="narration-relaxed" name="旁白-放松" intensity="2" role="neutral" roleName="默认"><s line="1">也没有随礼只是吃了一顿饭</s><s line="2">阴暗爬行创飞所有人</s></emotion></speak></root>')
    encode_str = base64.b64encode(html_str.encode('utf-8')).decode('utf-8')

    return encode_str

class ReqVoiceSignals(QObject):
    """定义信号的类"""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)

class ReqVoiceTask(QRunnable):

    _token = None
    _voic_cfg = None
    _clip_path = os.getcwd()
    _gen_voice_url = 'https://s.lang123.top/proxy/api/task/Audition'
    signals = ReqVoiceSignals()

    def __init__(self, word, idx):
        super().__init__()
        self.word = word
        self.idx = idx
        self.try_times = 5

    def down_load_audio(self, audio_url):
        response = requests.get(audio_url, stream=True)
        self.try_times -= 1
        if self.try_times < 0:
            self.signals.finished.emit({'sucess': False, "msg":'下载配音失败'})

        # 检查请求是否成功
        if response.status_code == 200:
            # 文件名可以根据 URL 或响应头中的内容设置
            file_type = audio_url.split('.')[-1]

            filename = f'配音片段_{self.idx}.{file_type}'
            # 计算文件的 MD5 哈希值
            md5 = hashlib.md5()
            # 保存文件
            with open(self._clip_path + filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):  # 以 8KB 的块大小读取文件
                    file.write(chunk)
                    md5.update(chunk)

            print(f"{self.word} 文件已保存为 {filename}")
            print(f"文件的 MD5 哈希值: {md5.hexdigest()}")
            self.signals.finished.emit({'sucess': True, 'idx':self.idx, 'size':len(self.word)})
        else:
            print(f"下载失败，状态码: {response}")
            self.down_load_audio(audio_url)

    def run(self):
        payload = {'taskText': encode_word(self.word, self._voic_cfg)}
        params = {'token': self._token}
        response = requests.post(self._gen_voice_url, params=params, json=payload)
        data = response.json()
        print(f'code:{data['code']}, message:{data['message']}')
        if data.get('data') and data.get('data').get('audioUrl'):
            audio_url = data.get('data').get('audioUrl')
            self.down_load_audio(audio_url)
        elif data['code'] == 40600:
            time.sleep(8)
            self.run()
        elif data['code'] == 40302:
            self.signals.finished.emit({'need_login': True})
        else:
            self.signals.finished.emit({'sucess': False, 'msg': data.get('message')})


class WaitLoginThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, parent, uuid):
        super().__init__(parent)
        self.login_uuid = uuid
        self.running = True

    def run(self):
        check_login_url = 'https://s.lang123.top/proxy/api/user/GetLoginQrcodeState'
        params = {'uuid': self.login_uuid}
        response = requests.get(check_login_url, params=params)
        data = response.json()

        while self.running and data.get('data') and data['data']['state'] == 0:
            response = requests.get(check_login_url, params=params)
            data = response.json()
            self.usleep(1)

        if data['data'].get('token'):
            self.finished.emit(data['data'])


    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class TextToVoice():
    def __init__(self):
        self.qrcode_url = 'https://s.lang123.top/proxy/api/user/GetLoginQrcode'
        self.login_file_path = os.getcwd() + '/登录信息'
        os.makedirs(self.login_file_path, exist_ok=True)
        self.login_data = None
        self.get_login_data()

        self.voice_cfg_path = os.getcwd() + '/声音配置.json'
        self.get_voice_cfg()

    # _voice_list = [{'name':'云希Pro','voice':'azure_zh-CN-YunxiNeural','hostType':6,'volume':1,'pitch':0,'rate':1.4,
    #                 'emotion':{'category':'narration-relaxed','name':'旁白-放松','intensity':2,'role':'YoungAdultMale','roleName':'男青年'}},
    #                {'name': '晓辰Pro', 'voice': 'ttson_257', 'hostType': 6, 'volume': 1, 'pitch': 0,'rate': 1.4,
    #                 'emotion': {'category': 'neutral', 'name': '默认', 'intensity': 2,'role': 'YoungAdultMale', 'roleName': '男青年'}}]

    def get_voice_cfg(self):
        with open(self.voice_cfg_path, 'r', encoding='utf-8') as json_file:
            self.voice_cfg = json.load(json_file)

    def get_login_data(self):
        file_path = self.login_file_path + '/登录信息.json'
        with open(file_path, 'a+', encoding='utf-8') as json_file:
            json_file.seek(0)
            content = json_file.read()
            if content.strip():
                json_file.seek(0)
                self.login_data = json.load(json_file)
        return self.login_data

    def set_login_data(self, data):
        file_path = self.login_file_path + '/登录信息.json'
        self.login_data = {'token':data.get("token")}
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(self.login_data, json_file, indent=4)

    def get_login_qrcode(self):
        response = requests.get(self.qrcode_url)
        if response.status_code == 200:
            data = response.json()

            base64_data = data['data']['qrcode']
            # 将 Base64 编码解码为二进制数据
            image_data = base64.b64decode(base64_data)

            self.login_uuid = data['data']['uuid']
            # 将二进制数据保存为 JPEG 文件
            with (open(self.login_file_path + "/login_qrcode.jpg", "wb") as image_file):
                image_file.write(image_data)

            return self.login_file_path + "/login_qrcode.jpg"









