from PyQt6.QtCore import QObject, pyqtSignal


class VoiceLines(QObject):

    data_change = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.line_list = []

    # change_src 1 修改源于主界面 2 源于分镜界面 3 读取srt文件
    def set_list(self, list, change_src):
        self.line_list = list

        self.data_change.emit({'change_src':change_src})




voice_text_lines = VoiceLines()