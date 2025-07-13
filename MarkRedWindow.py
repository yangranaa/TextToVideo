import os

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QFrame, QLineEdit, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QScrollArea

from FileTool import save_json_file, load_json_file


class MarkRedData:
    data_path = 'mark_red.json'

    word_list = []

    @classmethod
    def remove_data(cls, word):
        cls.word_list.remove(word)
        cls.save_data()

    @classmethod
    def load_from_file(cls):
        if os.path.isfile(cls.data_path):
            cls.word_list = load_json_file(cls.data_path)

    @classmethod
    def save_data(cls):
        save_json_file(cls.data_path, cls.word_list)


class MarkRedItem(QFrame):
    btn_event = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.red_word = QLineEdit()
        layout.addWidget(self.red_word)

        self.del_btn = QPushButton('删除')
        self.del_btn.clicked.connect(self.emit_del)
        layout.addWidget(self.del_btn, stretch=1)

    def emit_del(self):
        self.btn_event.emit({"del": True, "item": self})

class MarkRedWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.Window)  # 关键设置
        self.setWindowTitle("标红词")
        self.resize(1660, 800)  # 设置窗口大小

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        menu_layout = QHBoxLayout()
        main_layout.addLayout(menu_layout)

        self.add_item = QPushButton("添加关键字")
        self.add_item.clicked.connect(self.create_item)
        menu_layout.addWidget(self.add_item)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)

        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.items = []
        self.refresh_items()

        self.show()

    def hand_item_btn(self, dict):
        item_idx = self.items.index(dict['item'])

        if dict.get('del'):
            self.del_item(item_idx)

    def create_item(self, word=None):
        item = MarkRedItem()
        if word:
            item.red_word.setText(word)

        item.red_word.textChanged.connect(self.set_replace_data)
        item.btn_event.connect(self.hand_item_btn)

        self.scroll_layout.addWidget(item)
        self.items.append(item)

        return item

    def del_item(self, item_idx):
        item = self.items.pop(item_idx)
        self.scroll_layout.removeWidget(item)
        self.scroll_layout.update()
        item.setVisible(False)
        item.deleteLater()

        self.set_replace_data()

    def set_replace_data(self):
        MarkRedData.word_list.clear()
        for idx,item in enumerate(self.items):
            MarkRedData.word_list.append(item.red_word.text())

        MarkRedData.save_data()

    def refresh_items(self):
        for word in MarkRedData.word_list:
            self.create_item(word)