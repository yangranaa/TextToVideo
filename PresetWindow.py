import os.path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QHBoxLayout, QPushButton, QScrollArea, QLineEdit, QLabel

from FileTool import save_json_file, load_json_file


class PresetData:
    data_path = 'preset_promt.json'

    preset_dic = {}

    @classmethod
    def remove_data(cls, name):
        cls.preset_dic.pop(name)
        cls.save_data()

    @classmethod
    def update_data(cls, name, promt):
        cls.preset_dic[name] = promt
        cls.save_data()

    @classmethod
    def load_from_file(cls):
        if os.path.isfile(cls.data_path):
            cls.preset_dic = load_json_file(cls.data_path)


    @classmethod
    def save_data(cls):
        save_json_file(cls.data_path, cls.preset_dic)


class PresetItem(QFrame):

    btn_event = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.preset_name = QLineEdit()
        layout.addWidget(self.preset_name, stretch=1)

        self.preset_promt = QLineEdit()
        layout.addWidget(self.preset_promt, stretch=10)

        self.del_btn = QPushButton('删除')
        self.del_btn.clicked.connect(self.emit_del)
        layout.addWidget(self.del_btn, stretch=1)

    def emit_del(self):
        self.btn_event.emit({"del": True, "preset_item": self})

class PresetWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.Window)  # 关键设置
        self.setWindowTitle("预设角色场景关键词")
        self.resize(1660, 800)  # 设置窗口大小

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.main_frame = QFrame(self)
        main_layout.addWidget(self.main_frame)
        menu_layout = QHBoxLayout()
        self.main_frame.setLayout(menu_layout)

        self.style_lab = QLabel('风格:')
        menu_layout.addWidget(self.style_lab)

        self.style_line = QLineEdit("")
        self.style_line.textChanged.connect(self.set_preset_data)
        menu_layout.addWidget(self.style_line)

        self.add_preset = QPushButton("添加预设")
        self.add_preset.clicked.connect(self.create_item)
        menu_layout.addWidget(self.add_preset)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)

        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.preset_items = []
        self.refresh_items()

        self.show()

    def hand_item_btn(self, dict):
        item_idx = self.preset_items.index(dict['preset_item'])

        if dict.get('del'):
            self.del_preset_item(item_idx)

    def del_preset_item(self, item_idx):
        preset_item = self.preset_items.pop(item_idx)
        self.scroll_layout.removeWidget(preset_item)
        self.scroll_layout.update()
        preset_item.setVisible(False)
        preset_item.deleteLater()

        self.set_preset_data()

    def create_item(self, name=None, promt=None):
        preset_item = PresetItem()
        if name:
            preset_item.preset_name.setText(name)
            preset_item.preset_promt.setText(promt)

        preset_item.preset_promt.textChanged.connect(self.set_preset_data)
        preset_item.preset_name.textChanged.connect(self.set_preset_data)
        preset_item.btn_event.connect(self.hand_item_btn)

        self.scroll_layout.addWidget(preset_item)
        self.preset_items.append(preset_item)

        return preset_item

    def refresh_items(self):
        for name,promt in PresetData.preset_dic.items():
            if name != 'style':
                self.create_item(name, promt)

        if PresetData.preset_dic.get('style'):
            self.style_line.setText(PresetData.preset_dic['style'])

    def set_preset_data(self):
        PresetData.preset_dic.clear()
        for item in self.preset_items:
            name = item.preset_name.text()
            promt = item.preset_promt.text()
            PresetData.preset_dic[name] = promt

        PresetData.preset_dic['style'] = self.style_line.text()

        PresetData.save_data()

