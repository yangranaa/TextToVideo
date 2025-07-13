import os

from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QScrollArea, QHBoxLayout, QPushButton, QComboBox, QLineEdit, \
    QLabel

from FileTool import load_json_file, save_json_file
from QtLayoutCss import layout_css_str

agent_key_set_config = {
    "讯飞":{"API Secret":"","API Key":"","API Flowid":""},
    "文心":{"ID":"","密钥":""},
    "腾讯":{"app_key":""},
    "智谱":{"api_key":""}
}

class AIKeyChangeSingal(QObject):

    data_change = pyqtSignal(dict)

class AIKeyData:
    data_path = 'ai_key.json'

    ai_list = []

    signal = AIKeyChangeSingal()

    @classmethod
    def load_from_file(cls):
        if os.path.isfile(cls.data_path):
            cls.ai_list = load_json_file(cls.data_path)
        else:
            for ai_type in agent_key_set_config.keys():
                cls.create_data(ai_type)


    @classmethod
    def create_data(cls, ai_type):
        key_set = {'name': 'no_name', 'type': ai_type, 'keys': {}}
        config = agent_key_set_config[ai_type]

        for key_name, key in config.items():
            key_set['keys'][key_name] = key

        cls.ai_list.append(key_set)

        cls.on_data_change()

        return key_set

    @classmethod
    def remove_data(cls, key_set):
        cls.ai_list.remove(key_set)

        cls.on_data_change()

    @classmethod
    def on_data_change(cls):
        cls.signal.data_change.emit({'data_change': True})
        cls.save_data()

    @classmethod
    def save_data(cls):
        save_json_file(cls.data_path, cls.ai_list)

class AgentSetingItem(QFrame):

    def __init__(self, key_set):
        super().__init__()

        self.key_set = None
        self.key_items = []

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.ai_type_combox = QComboBox()
        layout.addWidget(self.ai_type_combox)

        for ai_type, _ in agent_key_set_config.items():
            self.ai_type_combox.addItem(ai_type)

        self.ai_type_combox.currentIndexChanged.connect(self.ai_type_changed)

        self.ai_name_edit = QLineEdit(key_set['name'])
        layout.addWidget(self.ai_name_edit)

        self.keys_layout = QVBoxLayout()
        layout.addLayout(self.keys_layout)

        self.del_btn = QPushButton('删除')
        self.del_btn.clicked.connect(self.del_set)
        layout.addWidget(self.del_btn)

        self.set_data(key_set)

    def on_set_change(self):
        self.key_set['name'] = self.ai_name_edit.text()
        self.key_set['type'] = self.ai_type_combox.currentText()

        self.key_set['keys'] = {}
        for key_item in self.key_items:
            if key_item['enable']:
                self.key_set['keys'][key_item['key_name'].text()] = key_item['key'].text()

        # AIKeyData.on_data_change()

    def set_data(self, key_set):
        self.key_set = key_set

        idx = self.ai_type_combox.findText(key_set['type'], Qt.MatchFlag.MatchExactly)
        if idx == self.ai_type_combox.currentIndex():
            self.ai_type_changed(idx)
        else:
            self.ai_type_combox.setCurrentIndex(idx)

    def del_set(self):
        AIKeyData.remove_data(self.key_set)

    def ai_type_changed(self, idx):
        for key_item in self.key_items:
            key_item['frame'].setVisible(False)
            key_item['enable'] = False

        ai_type = self.ai_type_combox.currentText()

        config = agent_key_set_config[ai_type]
        key_datas = None
        if ai_type == self.key_set['type']:
            key_datas = self.key_set['keys']

        count = 0
        for key_name, _ in config.items():
            key_item = self.get_key_item(count)
            key_item['frame'].setVisible(True)
            key_item['enable'] = True
            key_item['key_name'].setText(key_name)
            if key_datas:
                key_item['key'].setText(key_datas[key_name])
            else:
                key_item['key'].setText('')

            count += 1

    def get_key_item(self, idx):
        if len(self.key_items) > idx:
            return self.key_items[idx]
        else:
            key_item_layout = QVBoxLayout()
            key_item_layout.activate()

            key_item_frame = QFrame()
            key_item_frame.setLayout(key_item_layout)

            self.keys_layout.addWidget(key_item_frame)

            key_item = {'key_name':QLabel(""), 'key':QLineEdit(""), 'frame': key_item_frame, 'enable':True}

            key_item_layout.addWidget(key_item['key_name'])
            key_item_layout.addWidget(key_item['key'])

            key_item['key'].textChanged.connect(self.on_set_change)

            self.key_items.append(key_item)

            return key_item

class AgentSetingView(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.Window)  # 关键设置
        self.setWindowTitle("填写AI访问密钥")
        self.resize(1660, 800)  # 设置窗口大小

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.setStyleSheet(layout_css_str)

        self.main_frame = QFrame(self)
        main_layout.addWidget(self.main_frame)
        menu_layout = QHBoxLayout()
        self.main_frame.setLayout(menu_layout)

        self.add_AI = QPushButton("添加生图AI")
        self.add_AI.clicked.connect(self.add_item)
        menu_layout.addWidget(self.add_AI)

        self.save_AI_set_btn = QPushButton("保存")
        self.save_AI_set_btn.clicked.connect(AIKeyData.save_data)
        menu_layout.addWidget(self.save_AI_set_btn)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)

        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.show()

        self.ai_setting_items = []
        self.refresh_items()

        AIKeyData.signal.data_change.connect(self.refresh_items)

    def add_item(self):
        AIKeyData.create_data("讯飞")

    def create_item(self, ai_set):
        ai_setting_item = AgentSetingItem(ai_set)

        self.scroll_layout.addWidget(ai_setting_item)
        self.ai_setting_items.append(ai_setting_item)

        return ai_setting_item

    def get_item(self, idx, key_set):
        if len(self.ai_setting_items) > idx:
            item = self.ai_setting_items[idx]
            item.set_data(key_set)
        else:
            item = self.create_item(key_set)

        return item

    def refresh_items(self):
        for item in self.ai_setting_items:
            item.setVisible(False)

        for idx, ai_set in enumerate(AIKeyData.ai_list):
            item = self.get_item(idx, ai_set)
            item.setVisible(True)
