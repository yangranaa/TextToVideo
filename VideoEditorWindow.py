import os

from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog, QFrame, QScrollArea, \
     QComboBox, QCheckBox

from AgentManager import AgentManager
from AgentSetingView import AgentSetingView, AIKeyData
from GlobalSignals import global_signals
from MarkRedWindow import MarkRedData
from NoticeManager import NoticeManager
from PresetWindow import PresetWindow, PresetData
from PromtWindow import PromtWindow
from ReplaceWindow import ReplaceData
from ShotData import ShotData
from ShotItem import ShotItem
from VoiceText import voice_text_lines


class VideoEditorWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.ai_setting_view = None
        self.preset_editor = None
        self.gen_shot_view = None

        self.setWindowFlags(Qt.WindowType.Window)  # 关键设置
        self.setWindowTitle("图文编辑")
        self.resize(1660, 800)  # 设置窗口大小

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.main_frame = QFrame(self)
        main_layout.addWidget(self.main_frame)

        menu_layout = QHBoxLayout()
        self.main_frame.setLayout(menu_layout)

        self.gen_text_btn = QPushButton("整理全文")
        self.gen_text_btn.clicked.connect(self.gen_text)
        menu_layout.addWidget(self.gen_text_btn)

        self.load_shot_btn = QPushButton("加载分镜")
        self.load_shot_btn.clicked.connect(self.load_shot)
        menu_layout.addWidget(self.load_shot_btn)

        self.insert_shot = QPushButton("插入分镜")
        self.insert_shot.clicked.connect(self.insert_first)
        menu_layout.addWidget(self.insert_shot)

        self.open_preset_window = QPushButton("管理预设")
        self.open_preset_window.clicked.connect(self.open_preset_editor)
        menu_layout.addWidget(self.open_preset_window)

        self.open_ai_setting_btn = QPushButton("配置ai")
        self.open_ai_setting_btn.clicked.connect(self.open_ai_setting_view)
        menu_layout.addWidget(self.open_ai_setting_btn)

        AIKeyData.load_from_file()

        self.agent_comb = QComboBox()
        self.refresh_ai_combox()
        self.agent_comb.currentIndexChanged.connect(self.agent_changed)
        menu_layout.addWidget(self.agent_comb)
        AIKeyData.signal.data_change.connect(self.refresh_ai_combox)

        self.gen_all_pic_btn = QPushButton("生成空缺图")
        self.gen_all_pic_btn.clicked.connect(self.gen_all_pic)
        menu_layout.addWidget(self.gen_all_pic_btn)

        self.only_red_check = QCheckBox("只显红项")
        self.only_red_check.setCheckState(Qt.CheckState.Checked)
        self.only_red_check.stateChanged.connect(self.only_red_change)
        menu_layout.addWidget(self.only_red_check)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)

        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.shot_items = []

        PresetData.load_from_file()

        ShotData.read_data_from_file()
        self.refresh_items()

        global_signals.reset_shot_data.connect(self.refresh_items)

        self.show()
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.handle_scroll)
        self.handle_scroll()

    def refresh_ai_combox(self):
        for idx, agent in enumerate(AIKeyData.ai_list):
            if idx > self.agent_comb.count() - 1:
                self.agent_comb.addItem(agent['name'])
            else:
                self.agent_comb.setItemText(idx, agent['name'])

        for idx in range(len(AIKeyData.ai_list), self.agent_comb.count()):
            self.agent_comb.removeItem(idx)

    def shotdata_reset(self, dict):
        self.refresh_items()

    def agent_changed(self, idx):
        AgentManager.agent_idx = idx

    def insert_first(self):
        if len(voice_text_lines.line_list) == 0:
            NoticeManager.add_notice('先输入整理文本')
            return

        if len(ShotData.shot_datas) == 0:
            ShotData.gen_first_data()
            self.refresh_item(0)

    def handle_scroll(self):
        viewport = self.scroll_area.viewport()
        view_rect = viewport.rect()

        for item in self.shot_items:
            if not item.isVisible():
                continue

            item_pos = item.mapTo(viewport, QPoint(0, 0))
            item_rect = QRect(item_pos, item.size())

            # 判断是否与可视区域相交
            if view_rect.intersects(item_rect):
                item.set_active(True)  # 激活资源
            else:
                item.set_active(False)  # 释放资源


    def text_move(self, dict):
        item_idx = self.shot_items.index(dict['shot_item'])
        value = dict['delta']

        ShotData.move_shot_text(item_idx, value>0)

    def hand_shot_btn(self, dict):
        item_idx = self.shot_items.index(dict['shot_item'])

        if dict.get('del'):
            self.del_shot_item(item_idx)

        if dict.get('insert'):
            self.refresh_item(item_idx, True)

    def item_visible_change(self, dict):
        self.handle_scroll()

    def get_item(self, item_idx):
        if len(self.shot_items) > item_idx >= 0:
            return self.shot_items[item_idx]
        else:
            return None

    def del_shot_item(self, item_idx):
        shot_item = self.shot_items.pop(item_idx)
        self.scroll_layout.removeWidget(shot_item)
        self.scroll_layout.update()
        shot_item.setVisible(False)
        shot_item.deleteLater()

        ShotData.del_data(item_idx)

    def gen_text(self):

        for item in self.shot_items:
            item.text_content.blockSignals(True)

            text = item.text_content.toPlainText()

            for src, dst in ReplaceData.replace_dic.items():
                text = text.replace(src, dst)

            item.text_content.setPlainText(text)

            self.mark_red(item.text_content)
            item.text_content.blockSignals(False)

        self.set_voice_text()

    def mark_red(self, text_edit):

        for word in MarkRedData.word_list:

            red_format = QTextCharFormat()
            red_format.setForeground(QColor(220, 20, 60))

            document = text_edit.document()
            cursor = QTextCursor(document)

            cursor.movePosition(QTextCursor.MoveOperation.Start)
            while True:
                cursor = document.find(word, cursor)
                if cursor.isNull():
                    break

                cursor.mergeCharFormat(red_format)
                # cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, len(word))

            document.markContentsDirty(0, document.characterCount())

        text_edit.update()
        text_edit.repaint()

    def set_voice_text(self):
        line_list = []
        for item in self.shot_items:
            if item.shot_data is not None:
                item.shot_data.line_list = item.text_content.toPlainText().splitlines()

                for line in item.shot_data.line_list:
                    line_list.append(line)

        voice_text_lines.set_list(line_list, 2)

    def create_shot_item(self, index):
        shot_item = ShotItem()
        shot_item.text_content.text_move.connect(self.text_move)
        shot_item.btn_event.connect(self.hand_shot_btn)
        shot_item.visible_event.connect(self.item_visible_change)
        shot_item.text_content.textChanged.connect(self.set_voice_text)

        self.scroll_layout.insertWidget(index, shot_item)
        self.shot_items.insert(index, shot_item)

        return shot_item

    def only_red_change(self):
        ShotData.show_red = self.only_red_check.checkState() == Qt.CheckState.Checked

        self.refresh_items()

    def refresh_item(self, index, is_insert=False):
        if is_insert:
            shot_data = ShotData.insert_data(index, None)
            shot_item = self.create_shot_item(index)
        else:
            shot_data = ShotData.shot_datas[index]
            if len(self.shot_items) <= index:
                shot_item = self.create_shot_item(index)
            else:
                shot_item = self.shot_items[index]

        shot_item.set_shot_data(shot_data)


    def refresh_items(self):
        for shot_item in self.shot_items:
            shot_item.shot_data = None
            shot_item.set_visible(False)

        for idx, shot_data in enumerate(ShotData.shot_datas):
            self.refresh_item(idx)

    def sel_imgs(self):
        img_dir = QFileDialog.getExistingDirectory(self, "图片文件夹")

        if len(voice_text_lines.line_list) == 0 :
            NoticeManager.add_notice("先输入整理文本")
            return

        if img_dir:

            # self.imgs_lab.setText(img_dir)

            ShotData.gen_shot_datas(img_dir)

            self.refresh_items()

    def load_shot(self):
        if self.gen_shot_view is None:
            self.gen_shot_view = PromtWindow()

        self.gen_shot_view.show()
        self.gen_shot_view.refresh_ai_contrl()

    def open_preset_editor(self):
        if self.preset_editor is None:
            self.preset_editor = PresetWindow()

        self.preset_editor.show()

    def open_ai_setting_view(self):
        if self.ai_setting_view is None:
            self.ai_setting_view = AgentSetingView()

        self.ai_setting_view.show()

    def gen_all_pic(self):
        for shot_data in ShotData.shot_datas:
            if shot_data.img_path is None:
                shot_data.req_pic()
            else:
                shot_data.red = False

            shot_data.save_data()
            shot_data.emit_data_changed()