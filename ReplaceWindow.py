import os

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QFrame, QLineEdit, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QScrollArea, \
    QTextEdit

from FileTool import save_json_file, load_json_file


class ReplaceData:
    data_path = 'replace_word.json'

    replace_dic = {}

    @classmethod
    def remove_data(cls, src):
        cls.replace_dic.pop(src)
        cls.save_data()

    @classmethod
    def update_data(cls, src, dst):
        cls.replace_dic[src] = dst
        cls.save_data()

    @classmethod
    def load_from_file(cls):
        if os.path.isfile(cls.data_path):
            cls.replace_dic = load_json_file(cls.data_path)

    @classmethod
    def save_data(cls):
        save_json_file(cls.data_path, cls.replace_dic)


class ReplaceItem(QFrame):
    btn_event = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.replace_src = QLineEdit()
        self.replace_lab = QLabel('替换')
        self.replace_dst = QTextEdit()

        layout.addWidget(self.replace_src)
        layout.addWidget(self.replace_lab)
        layout.addWidget(self.replace_dst)

        self.del_btn = QPushButton('删除')
        self.del_btn.clicked.connect(self.emit_del)
        layout.addWidget(self.del_btn, stretch=1)

    def emit_del(self):
        self.btn_event.emit({"del": True, "item": self})

class ReplaceWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.Window)  # 关键设置
        self.setWindowTitle("替换关键词")
        self.resize(1660, 800)  # 设置窗口大小

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        menu_layout = QHBoxLayout()
        main_layout.addLayout(menu_layout)

        self.add_item = QPushButton("添加替换")
        self.add_item.clicked.connect(self.create_item)
        menu_layout.addWidget(self.add_item)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)

        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.replace_items = []
        self.refresh_items()

        self.show()

    def hand_item_btn(self, dict):
        item_idx = self.replace_items.index(dict['item'])

        if dict.get('del'):
            self.del_item(item_idx)

    def create_item(self, src=None, dst=None):
        replace_item = ReplaceItem()
        if src:
            replace_item.replace_src.setText(src)
            replace_item.replace_dst.setPlainText(dst)

        replace_item.replace_src.textChanged.connect(self.set_replace_data)
        replace_item.replace_dst.textChanged.connect(self.set_replace_data)
        replace_item.btn_event.connect(self.hand_item_btn)

        self.scroll_layout.addWidget(replace_item)
        self.replace_items.append(replace_item)

        return replace_item

    def del_item(self, item_idx):
        item = self.replace_items.pop(item_idx)
        self.scroll_layout.removeWidget(item)
        self.scroll_layout.update()
        item.setVisible(False)
        item.deleteLater()

        self.set_replace_data()

    def set_replace_data(self):
        ReplaceData.replace_dic.clear()

        for item in self.replace_items:
            src = item.replace_src.text()
            dst = item.replace_dst.toPlainText()
            ReplaceData.replace_dic[src] = dst


        ReplaceData.save_data()

    def refresh_items(self):
        for src, dst in ReplaceData.replace_dic.items():
            self.create_item(src, dst)