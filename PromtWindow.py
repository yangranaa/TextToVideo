import os.path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton

from FileTool import load_json_file, save_json_file
from ShotData import ShotData
from VoiceText import voice_text_lines

ai_contrl_text = """
将输入文本按顺序划分为分镜画面，每个分镜中角色的动作、表情及所处环境，确保将全部原文内容划分
归纳所有角色的外形特征

每个分镜的格式为 [["原文句子1","原文句子2","原文句子3"], "分镜内容"]
分镜内容格式为"景别，(画面位置，人物名1，人物入镜部分，面向，表情，动作)，(画面位置，人物名2，人物入镜部分，面向，表情，动作)，背景环境"
分镜描述静止画面, 是用于文生图的提示词，不要多人物交互内容 例如(张三跑向李四)
要确保原文句子攘括全文，单个分镜内容不宜超过5句，画面主要人物也不要超过3个，背景人群数量不限制

每个角色外形特征格式为 ["名字":"年龄，发型，衣着"]
特征是用于文生图的提示词

#输出示例：
{
    "juese": [
        ["张三":"年轻帅气男性，黑色长发飘逸，白色剑仙袍"],
        ["李四":"年轻女性，黑色长发飘逸，紫色连衣裙，白色发箍"]
    ],

    "fenjing": [
        [["原文句子1","原文句子2","原文句子3"], "远景，(画面中央，李四，全身，面向左，仰头微笑，向前跑)，围观人群表情惊讶，大型喷泉广场"],
        [["原文句子4","原文句子5","原文句子6","原文句子7"], "中景，(画面左边，张三，上半身，面向右，微笑，手指指向右)(画面右边，李四，上半身，面向左，闭眼睛)，办公室内，墙上挂着锦旗"],
        [["原文句子8","原文句子9","原文句子10"], "近景，(画面左边，张三，脸特写，面向前，低头哭泣，抹眼泪)(画面左边，李四，脸特写，面向右，张嘴说话)，荒郊野外"]
    ]
}
输入文本是:
"""

class PromtWindow(QWidget):

    prompt_fmt_file = "prompt_fmt.json"

    def __init__(self):
        super().__init__()

        self.cache_promt = []

        self.setWindowFlags(Qt.WindowType.Window)  # 关键设置
        self.setWindowTitle("生成分镜")
        self.resize(800, 600)  # 设置窗口大小

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.ai_contrl_edit = QTextEdit()
        self.ai_contrl_edit.textChanged.connect(self.save_prompt_fmt)
        main_layout.addWidget(self.ai_contrl_edit)

        gen_shot_layout = QHBoxLayout()
        main_layout.addLayout(gen_shot_layout)

        self.text_edit = QTextEdit()
        gen_shot_layout.addWidget(self.text_edit)

        self.gen_shot_btn = QPushButton("生成分镜")
        self.gen_shot_btn.clicked.connect(self.gen_shot)
        gen_shot_layout.addWidget(self.gen_shot_btn)

        self.show()

    def refresh_ai_contrl(self):

        lines = '\n'.join(voice_text_lines.line_list)

        if os.path.isfile(self.prompt_fmt_file):
            text = load_json_file(self.prompt_fmt_file)['text']
        else:
            text = ai_contrl_text

        text = f'{text}({lines})'
        self.ai_contrl_edit.setPlainText(text)

    def save_prompt_fmt(self):
        fmt = self.ai_contrl_edit.toPlainText().split("输入文本是:")[0]
        fmt += "输入文本是:"
        data = {'text':fmt}
        save_json_file(self.prompt_fmt_file, data)

    def gen_shot(self):
        ShotData.gen_shot_datas_by_data(self.text_edit.toPlainText())