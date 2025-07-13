from PyQt6.QtCore import Qt, QMimeData, QUrl, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QDrag, QWheelEvent, QTextCharFormat, QColor, QSyntaxHighlighter, QPixmap
from PyQt6.QtWidgets import QApplication, QComboBox, QPushButton, QLabel, QVBoxLayout, QTextEdit, QHBoxLayout, QFrame, \
    QPlainTextEdit, QGridLayout, QSizePolicy

from ShotEffConfig import shot_eff_config, find_eff_index, shot_enter_eff_config, find_enter_eff_index, \
    shot_after_eff_config, find_after_eff_idx
from GLWidget import GLWidget
from PresetWindow import PresetData
from QtLayoutCss import layout_css_str
from ShotData import ShotData


class KeywordHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setForeground(QColor(70, 130, 180))  # 设置蓝色字体

    def highlightBlock(self, text):
        for keyword in PresetData.preset_dic.keys():
            pattern = QRegularExpression(f"{keyword}")  # 使用单词边界匹配
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, self.highlight_format)


class ShotText(QPlainTextEdit):
    text_move = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()  # 垂直滚动量

        self.text_move.emit({'shot_item':self.parent,'delta':delta})

        event.accept()

class BackupImg(QLabel):

    clicked = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        # self.setScaledContents(True)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Ignored)
        self.setMinimumSize(1, 1)

        self.setScaledContents(True)

        self.img_path = None


    def set_img(self, img_path):
        self.img_path = img_path
        pixmap = QPixmap(img_path)
        # scaled_pixmap = pixmap.scaled(self.size(),
        #                               Qt.AspectRatioMode.IgnoreAspectRatio,
        #                               Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(pixmap)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        """处理鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit({"backup_item":self})  # 发射点击信号

class ShotItem(QFrame):

    btn_event = pyqtSignal(dict)
    visible_event = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.is_active = None
        self.is_visible = None

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.setStyleSheet(layout_css_str)

        self.text_content = ShotText(self)
        # self.text_content.setReadOnly(True)
        layout.addWidget(self.text_content, stretch=3)

        self.promt_edit = QTextEdit()
        self.promt_edit.textChanged.connect(self.on_promt_change)
        self.high_lighter = KeywordHighlighter(self.promt_edit.document())
        layout.addWidget(self.promt_edit, stretch=2)

        self.gl_widget = GLWidget()
        layout.addWidget(self.gl_widget, stretch=5)
        self.gl_widget.set_fixed_view_port(512,384)

        backup_layout = QGridLayout()
        layout.addLayout(backup_layout, stretch=5)

        backup_layout.setSpacing(0)
        backup_layout.setContentsMargins(0,0,0,0)

        self.backup_items = []
        # for i in range(2):
        #     backup_layout.setRowStretch(i, 1)
        #     backup_layout.setColumnStretch(i, 1)

        for i in range(2):
            for j in range(2):
                img_item = BackupImg()
                img_item.clicked.connect(self.on_img_item_click)
                backup_layout.addWidget(img_item, i, j)
                self.backup_items.append(img_item)

        btn_layout = QVBoxLayout()
        layout.addLayout(btn_layout, stretch=1)

        self.insert_shot = QPushButton("插入分镜")
        self.insert_shot.clicked.connect(self.emit_insert)
        btn_layout.addWidget(self.insert_shot)

        self.del_shot = QPushButton("删除分镜")
        self.del_shot.clicked.connect(self.emit_del)
        btn_layout.addWidget(self.del_shot)

        self.gen_pic_lab = QLabel("生图中...")
        btn_layout.addWidget(self.gen_pic_lab)

        self.gen_img_btn = QPushButton("生图")
        self.gen_img_btn.clicked.connect(self.gen_img)
        btn_layout.addWidget(self.gen_img_btn)

        self.clear_img_btn = QPushButton("清除图像")
        self.clear_img_btn.clicked.connect(self.clear_img)
        btn_layout.addWidget(self.clear_img_btn)


        self.enter_eff_comb = QComboBox()
        btn_layout.addWidget(self.enter_eff_comb)
        for eff_config in shot_enter_eff_config:
            self.enter_eff_comb.addItem(eff_config[0])

        self.enter_eff_comb.currentIndexChanged.connect(self.enter_eff_changed)

        self.eff_comb = QComboBox()
        btn_layout.addWidget(self.eff_comb)
        for eff_config in shot_eff_config:
            self.eff_comb.addItem(eff_config[0])

        self.eff_comb.currentIndexChanged.connect(self.eff_changed)

        self.after_eff_comb = QComboBox()
        btn_layout.addWidget(self.after_eff_comb)
        for eff_config in shot_after_eff_config:
            self.after_eff_comb.addItem(eff_config[0])

        self.after_eff_comb.currentIndexChanged.connect(self.after_eff_changed)

        self.setAcceptDrops(True)

    def set_shot_data(self, shot_data):
        self.shot_data = shot_data
        self.shot_data.data_change.connect(self.update_item)
        self.update_item()

    def on_promt_change(self):
        self.shot_data.promt = self.promt_edit.toPlainText()
        ShotData.save_data()

    def on_img_item_click(self, dic):
        img_item = dic.get('backup_item')

        if img_item.img_path:
            self.shot_data.img_path = img_item.img_path

        self.shot_data.save_data()
        self.shot_data.emit_data_changed()

    def emit_insert(self):
        self.btn_event.emit({"insert":True,"shot_item":self})

    def emit_del(self):
        self.btn_event.emit({"del":True, "shot_item": self})

    def set_text(self, text):
        self.text_content.setPlainText(text)

    def update_line(self):
        if len(self.shot_data.line_list) > 0:
            text = '\n'.join(self.shot_data.line_list)
            self.set_text(text)
        else:
            self.set_text('')

    def update_gl_window(self):
        idx = find_eff_index(self.shot_data.eff)
        self.eff_comb.setCurrentIndex(idx)

        idx = find_enter_eff_index(self.shot_data.enter_eff)
        self.enter_eff_comb.setCurrentIndex(idx)

        idx = find_after_eff_idx(self.shot_data.after_eff)
        self.after_eff_comb.setCurrentIndex(idx)

        self.refresh_shader()

    def update_backup_imgs(self):
        for idx, img_item in enumerate(self.backup_items):
            if idx < len(self.shot_data.backup_imgs):
                img_item.set_img(self.shot_data.backup_imgs[idx])


    def update_pic_gen(self):
        self.promt_edit.setPlainText(self.shot_data.promt)

        self.setProperty('red_mode', self.shot_data.red)
        self.style().unpolish(self)
        self.style().polish(self)

        if self.shot_data.req_err is None:
            self.gen_pic_lab.setText('生图中...')
        else:
            self.gen_pic_lab.setText(self.shot_data.req_err)

        hide_lab = self.shot_data.req_thread is None and self.shot_data.req_err is None

        self.gen_pic_lab.setVisible(not hide_lab)

        self.update_backup_imgs()

    def update_item(self):
        self.set_active(False)
        self.set_active(True)
        if ShotData.show_red:
            if self.shot_data.red:
                self.set_visible(True)
            else:
                self.set_visible(False)
        else:
            self.set_visible(True)

        self.update_line()

        self.update_gl_window()

        self.update_pic_gen()


    def set_visible(self, is_visible):
        if self.is_visible == is_visible:
            return

        self.is_visible = is_visible

        self.setVisible(self.is_visible)

        self.visible_event.emit({"visible_change":is_visible, "shot_item": self})

    def set_active(self, is_active):
        if self.is_active == is_active:
            return

        self.is_active = is_active

        if is_active:
            self.gl_widget.timer.start()
            self.refresh_shader()
        else:
            self.gl_widget.timer.stop()

    def enter_eff_changed(self, index):
        self.shot_data.enter_eff = shot_enter_eff_config[index][1]
        self.refresh_shader()
        ShotData.save_data()

    def eff_changed(self, index):
        self.shot_data.eff = shot_eff_config[index][1]
        self.refresh_shader()
        ShotData.save_data()

    def after_eff_changed(self, index):
        self.shot_data.after_eff = shot_after_eff_config[index][1]
        self.refresh_shader()
        ShotData.save_data()

    def refresh_shader(self):
        if self.shot_data.img_path:
            self.gl_widget.set_fixed_shader(self.shot_data.img_path,
                                            self.shot_data.eff,
                                            self.shot_data.enter_eff,
                                            self.shot_data.after_eff)
            # size = get_img_size(self.shot_data.img_path)
            # if size[0] >= 1024:
            #     w,h = int(size[0] * 0.5), int(size[1] * 0.5)
            #     self.gl_widget.setFixedSize(w,h)
            # else:
            #     self.gl_widget.setFixedSize(size[0], size[1])
        else:
            self.gl_widget.clear_shader = True
            # self.gl_widget.setFixedSize(400, 200)

    def clear_img(self):
        self.shot_data.img_path = None
        self.refresh_shader()
        ShotData.save_data()

    def gen_img(self):
        self.shot_data.req_pic()
        self.shot_data.emit_data_changed()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        # 获取文件路径列表
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls]
        event.acceptProposedAction()

        self.shot_data.img_path = file_paths[0]
        self.refresh_shader()
        ShotData.save_data()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and \
                (event.pos() - self.start_pos).manhattanLength() >= QApplication.startDragDistance():

            if self.shot_data.img_path:

                drag = QDrag(self)
                mime_data = QMimeData()
                url = QUrl.fromLocalFile(self.shot_data.img_path)

                self.shot_data.img_path = None
                ShotData.save_data()
                self.shot_data.emit_data_changed()

                mime_data.setUrls([url])
                drag.setMimeData(mime_data)
                drag.exec(Qt.DropAction.MoveAction)