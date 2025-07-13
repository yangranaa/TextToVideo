
import os
import random
import webbrowser

import torch

from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QThreadPool, QUrl
from PyQt6.QtGui import QTextCharFormat, QFont, QColor, QTextCursor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout, QCheckBox, QTextEdit, \
    QComboBox, QLineEdit, QSlider, QTabWidget, QWidget

from AudioOpThread import AudioOpThread
from FileTool import delete_files_in_folder, delete_file, open_folder
from GenVoice import GenVoice, GenVoiceTask, voice_models
from GlobalData import GlobalData
from JianYingManager import JianYingManager, JianYingOpThread
from MarkRedWindow import MarkRedWindow, MarkRedData
from NoticeManager import NoticeManager
from QtLayoutCss import web_btn_css
from ReplaceWindow import ReplaceWindow, ReplaceData
from STTModel import STTModel
from AudioTool import gen_srt_file
from ShotData import ShotData
from TextTool import gen_txt
from VoiceClone import VoiceClone, GenVoiceCloneTask
from VoiceText import voice_text_lines


class LeftFrame(QFrame):


    def __init__(self, parent):
        super().__init__(parent)
        parent.finished.connect(self.release)

        self.init_ui()
        self.anime_timers = []
        self.gen_jian_ying_cb = None
        self.gen_jian_ying_err = None
        self.gen_voice_cb = None
        self.model_idx = None
        self.jian_ying_op_thread = None

        MarkRedData.load_from_file()
        ReplaceData.load_from_file()
        self.replace_window = None
        self.mark_red_window = None

        self.thread_pool = QThreadPool().globalInstance()
        self.cur_setting = None
        self.thread_pool.setMaxThreadCount(1)

    def set_save_path(self):
        new_path = QFileDialog.getExistingDirectory(self, "保存路径")
        if new_path:
            GlobalData().set_save_path(new_path)
            self.save_path.setText(new_path)
            self.check_voice_path()
            self.check_srt_file()


    def set_clone_path(self):
        voice_clone_path, _ = QFileDialog.getOpenFileName(self, caption='请指定要克隆的声音，时长十五秒以内。', filter="Audio Files (*.wav)")
        if voice_clone_path:
            self.voice_clone_path.setText(voice_clone_path)
            GlobalData().voice_clone_path = voice_clone_path

    def set_jian_ying_path(self):
        new_path, _ = QFileDialog.getOpenFileName(self, caption='请指定剪映程序', filter="JianyingPro (*.exe)")
        if new_path:
            JianYingManager.jian_ying_path = new_path
            self.jian_ying_path.setText(new_path)

    def set_jian_ying_draft_path(self):
        new_path = QFileDialog.getExistingDirectory(self, caption='请指定剪映草稿文件中的textReading文件夹')
        if new_path:
            JianYingManager.jian_ying_draft_path = new_path
            self.jian_ying_draft_path.setText(new_path)

    @pyqtSlot(int)
    def voice_model_changed(self, index):
        self.model_idx = index
        model_name = self.sel_voice_model.itemText(index)
        self.refresh_voice_items(model_name)

        if GenVoice().select_model(model_name, self.check_voice_model):
            self.check_voice_model()
            NoticeManager.add_notice("正在加载配音模型")

    @pyqtSlot(int)
    def voice_changed(self, index):
        if index < 0:
            return
        self.voice_idx = index
        item_text = self.sel_voice_comb.itemText(index)
        self.sel_voice_name = item_text.split('|')[1]

    def refresh_voice_items(self, model_name):
        voices = voice_models[model_name]['voices']
        self.sel_voice_comb.clear()
        lan_name = {'a': "英语", 'z': '中文'}

        for language in ['z', 'a']:
            for voice in voices[language]:
                self.sel_voice_comb.addItem(f'{lan_name[language]}|{voice}')

    def del_voice(self):
        self.stop_play_voice()

        delete_file(GlobalData().voice_path)
        self.check_voice_path()

    def stop_play_voice(self):
        if self.media_play:
            self.media_play.stop()
            self.media_play.setSource(QUrl())

    def reset_voice(self):
        self.gen_finnal_voice()

    def play_voice(self):
        self.check_voice_path()

        if not self.media_play:
            self.media_play = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_play.setAudioOutput(self.audio_output)

        self.stop_play_voice()

        if os.path.exists(GlobalData().voice_clip_path):

            if not os.path.exists(GlobalData().voice_path):
                NoticeManager.add_notice("保存目录下不存在配音，开始拼接配音")

                self.gen_finnal_voice(call_back=self.play_voice)

                return
            else:

                new_setting = GlobalData().get_voice_setting()
                if self.cur_setting != new_setting:
                    NoticeManager.add_notice("设置变更开始调整配音")
                    self.gen_finnal_voice(new_setting, self.play_voice)
                    return

        else:
            NoticeManager.add_notice("保存目录下不存在配音片段，请先生成配音")
            return


        self.media_play.setSource(QUrl.fromLocalFile(GlobalData().voice_path))
        self.media_play.play()

    def speed_change(self, value):
        self.voice_speed = value * 0.01
        GlobalData().voice_speed = self.voice_speed
        self.speed_label.setText(f'语速：{self.voice_speed:.2f}')

    def pitch_change(self, value):
        self.voice_pitch = value * 0.1
        GlobalData().voice_pitch = self.voice_pitch
        self.pitch_label.setText(f'变调：{self.voice_pitch:.2f}')

    def volume_change(self, value):
        self.voice_volume = value * 0.01
        GlobalData().voice_volume = self.voice_volume
        self.volume_label.setText(f'音量：{self.voice_volume:.2f}')

    def voice_checked_change(self):
        GlobalData().cut_silent = self.cut_empty.checkState() == Qt.CheckState.Checked
        GlobalData().enhan_vocal = self.enhan_vocal.checkState() == Qt.CheckState.Checked
        GlobalData().save_data()

    def check_voice_clone_model(self):
        if VoiceClone.device is None:
            self.gen_clone_voice_btn.setText("生成配音(配音模型正在加载中…)")
            self.gen_clone_voice_btn.setEnabled(False)
        else:
            self.gen_clone_voice_btn.setText("生成配音")
            self.gen_clone_voice_btn.setEnabled(True)
            NoticeManager.add_notice("配音模型加载完成")

    def check_voice_model(self):
        if GenVoice().is_model_loading():
            self.gen_voice_btn.setText("生成配音(配音模型正在加载中…)")
            self.gen_voice_btn.setEnabled(False)
        else:
            self.gen_voice_btn.setText("生成配音")
            self.gen_voice_btn.setEnabled(True)
            NoticeManager.add_notice("配音模型加载完成")

    def on_jian_ying_op(self, msg):
        if msg.get('error'):
            NoticeManager.add_notice(msg.get('error'))
            if self.gen_jian_ying_err:
                self.gen_jian_ying_err()
        elif msg.get('finish'):
            NoticeManager.add_notice('剪映配音生成成功')

            last_draft_dir = JianYingManager.get_last_draft_path()
            if last_draft_dir:
                self.jian_ying_draft_path.setText(JianYingManager.last_draft_dir + "/textReading")

                self.connect_jian_ying_voice(self.gen_jian_ying_cb)
            else:
                self.jian_ying_draft_path.setText('无法识别草稿文件，请手动指定')
                NoticeManager.add_notice('无法识别草稿文件，请手动指定')

    def gen_jian_ying_voice(self, finish_cb=None, err_cb=None):
        self.gen_jian_ying_srt()
        self.gen_jian_ying_cb = finish_cb
        self.gen_jian_ying_err = err_cb
        self.jian_ying_op_thread = JianYingOpThread()
        self.jian_ying_op_thread.finished.connect(self.on_jian_ying_op)
        self.jian_ying_op_thread.start()

        NoticeManager.add_notice("开始加载逆向模型")
        STTModel.load_model_in_thread()

    def voice_tab_changed(self, index):
        if index == 1:
            self.sel_voice_model.setCurrentIndex(0)
            self.voice_model_changed(0)
        else:
            # NoticeManager.add_notice("释放配音模型")
            GenVoice().release()
            self.check_voice_model()

        if index == 2:
            self.check_voice_clone_model()
            if VoiceClone.device is None:
                NoticeManager.add_notice("开始加载克隆模型")
                VoiceClone.load_model_in_thread(self.check_voice_clone_model)
        else:
            # NoticeManager.add_notice("释放克隆模型")
            VoiceClone.release()

        if index != 0:
            STTModel.release()

    def init_voice_clone_tab(self):
        voice_clone_layout = QHBoxLayout()
        self.voice_clone_tab.setLayout(voice_clone_layout)

        self.voice_clone_path = QLineEdit("选取一个十秒左右的配音片段用于克隆")
        self.voice_clone_path.setReadOnly(True)
        voice_clone_layout.addWidget(self.voice_clone_path)

        self.voice_clone_path_btn = QPushButton("选取声音")
        self.voice_clone_path_btn.clicked.connect(self.set_clone_path)
        voice_clone_layout.addWidget(self.voice_clone_path_btn)

        self.gen_clone_voice_btn = QPushButton("生成配音")
        self.gen_clone_voice_btn.clicked.connect(self.gen_clone_voice)
        voice_clone_layout.addWidget(self.gen_clone_voice_btn)

    def init_local_voice_tab(self):
        local_voice_layout = QHBoxLayout()
        self.local_voice_tab.setLayout(local_voice_layout)

        device = 'gpu' if torch.cuda.is_available() else 'cpu'
        self.use_gpu_label = QLabel("生成模式：" + device)
        self.use_gpu_label.setToolTip("自动检测是否可用显卡加速")
        local_voice_layout.addWidget(self.use_gpu_label)

        self.sel_voice_model = QComboBox()
        local_voice_layout.addWidget(self.sel_voice_model)
        for model_name in voice_models.keys():
            self.sel_voice_model.addItem(model_name)
        self.sel_voice_model.currentIndexChanged.connect(self.voice_model_changed)

        self.sel_voice_comb = QComboBox()
        local_voice_layout.addWidget(self.sel_voice_comb)
        self.sel_voice_comb.currentIndexChanged.connect(self.voice_changed)

        self.gen_voice_btn = QPushButton("生成配音")
        self.gen_voice_btn.clicked.connect(self.gen_voice)
        local_voice_layout.addWidget(self.gen_voice_btn)

    def gen_jian_ying_srt(self):
        self.jian_ying_temp_path.setText("等待生成")

        delete_file(GlobalData().temp_srt_path)
        line_list = voice_text_lines.line_list

        for line in line_list:
            if line.strip() == '':
                NoticeManager.add_notice("存在空行先检查")
                return

        gen_srt_file(GlobalData().temp_srt_path, line_list)

        self.jian_ying_temp_path.setText(GlobalData().temp_srt_path)

    def change_jian_ying_model(self):
        self.jian_ying_auto_model = not self.jian_ying_auto_model

        is_auto_model = self.jian_ying_auto_model

        self.jian_ying_model_btn.setText("自动模式" if is_auto_model else "手动模式")

        self.hm_widget.setVisible(not is_auto_model)
        self.auto_widget.setVisible(is_auto_model)

        jian_ying_path = JianYingManager.get_jian_ying_app_path()
        if jian_ying_path:
            self.jian_ying_path.setText(jian_ying_path)
        else:
            self.jian_ying_path.setText("无法定位剪映程序，请手动指定")

        if is_auto_model:
            self.auto_model_layout.addWidget(self.jian_ying_path_lab)
            self.auto_model_layout.addWidget(self.jian_ying_path)
            self.auto_model_layout.addWidget(self.jian_ying_path_btn)

            self.auto_model_layout.addWidget(self.jian_ying_hint_lab)

            self.auto_model_layout.addWidget(self.gen_jian_ying_voice_btn)
        else:
            self.hm_model_layout.addWidget(self.jian_ying_temp_path)
            self.hm_model_layout.addWidget(self.jian_ying_srt_btn)

            self.hm_model_layout.addWidget(self.jian_ying_draft_path_lab)
            self.hm_model_layout.addWidget(self.jian_ying_draft_path)
            self.hm_model_layout.addWidget(self.jian_ying_draft_btn)

            self.hm_model_layout.addWidget(self.connect_voice_btn)

    def init_jian_ying_voice_tab(self):
        self.jian_ying_path_lab = QLabel("剪映：")
        self.jian_ying_path = QLineEdit("")
        self.jian_ying_path.setReadOnly(True)

        self.jian_ying_path_btn = QPushButton("剪映路径")
        self.jian_ying_path_btn.clicked.connect(self.set_jian_ying_path)

        self.jian_ying_hint_lab = QLabel("使用自动模式请双手离开鼠键。")

        self.jian_ying_temp_path = QLineEdit("等待生成")
        self.jian_ying_temp_path.setReadOnly(True)

        self.jian_ying_srt_btn = QPushButton("[1]生成srt")
        self.jian_ying_srt_btn.clicked.connect(self.gen_jian_ying_srt)

        self.jian_ying_draft_path_lab = QLabel("配音片段：")
        self.jian_ying_draft_path = QLineEdit("")
        self.jian_ying_draft_path.setReadOnly(True)

        self.gen_jian_ying_voice_btn = QPushButton("生成剪映配音")
        self.gen_jian_ying_voice_btn.clicked.connect(self.gen_jian_ying_voice)

        self.jian_ying_draft_btn = QPushButton("[2]片段路径")
        self.jian_ying_draft_btn.clicked.connect(self.set_jian_ying_draft_path)

        self.connect_voice_btn = QPushButton("[3]整合配音片段")
        self.connect_voice_btn.setToolTip("改变音量，减去空白音无需重新生成，点此按钮即可。")
        self.connect_voice_btn.clicked.connect(self.connect_jian_ying_voice)

        self.hm_widget = QWidget()
        self.hm_model_layout = QHBoxLayout()
        self.hm_widget.setLayout(self.hm_model_layout)

        self.auto_widget = QWidget()
        self.auto_model_layout = QHBoxLayout()
        self.auto_widget.setLayout(self.auto_model_layout)

        self.jian_ying_layout = QHBoxLayout()
        self.jian_ying_voice_tab.setLayout(self.jian_ying_layout)

        self.jian_ying_model_btn = QPushButton()
        self.jian_ying_model_btn.clicked.connect(self.change_jian_ying_model)
        self.jian_ying_layout.addWidget(self.jian_ying_model_btn)

        self.jian_ying_layout.addWidget(self.hm_widget)
        self.jian_ying_layout.addWidget(self.auto_widget)

        JianYingManager.get_jian_ying_app_path()
        self.jian_ying_auto_model = False

        self.change_jian_ying_model()


    def init_voice(self):
        self.media_play = None
        # 创建声音布局
        self.voice_frame = QFrame()
        self.frame_layout.addWidget(self.voice_frame, stretch=2)
        self.voice_layout = QVBoxLayout()
        self.voice_frame.setLayout(self.voice_layout)
        # ------------------------------------------------------------------
        self.voice_tab_widget = QTabWidget()
        self.voice_layout.addWidget(self.voice_tab_widget, stretch=1)

        self.jian_ying_voice_tab = QWidget()
        self.voice_tab_widget.addTab(self.jian_ying_voice_tab, "外部配音")
        self.init_jian_ying_voice_tab()

        self.local_voice_tab = QWidget()
        self.voice_tab_widget.addTab(self.local_voice_tab, "本地配音")
        self.init_local_voice_tab()

        self.voice_clone_tab = QWidget()
        self.voice_tab_widget.addTab(self.voice_clone_tab, "声音克隆")
        self.init_voice_clone_tab()

        self.voice_tab_widget.currentChanged.connect(self.voice_tab_changed)

        # ------------------------------------------------------------------

        voice_setting_layout = QHBoxLayout()
        self.voice_layout.addLayout(voice_setting_layout, stretch=1)

        check_state = Qt.CheckState.Checked if GlobalData().cut_silent else Qt.CheckState.Unchecked

        self.cut_empty = QCheckBox("剪去过长空白音")
        self.cut_empty.setCheckState(check_state)
        self.cut_empty.stateChanged.connect(self.voice_checked_change)
        voice_setting_layout.addWidget(self.cut_empty)

        check_state = Qt.CheckState.Checked if GlobalData().enhan_vocal else Qt.CheckState.Unchecked

        self.enhan_vocal = QCheckBox("声音美化")
        self.enhan_vocal.setCheckState(check_state)
        self.enhan_vocal.stateChanged.connect(self.voice_checked_change)
        voice_setting_layout.addWidget(self.enhan_vocal)

        self.speed_label = QLabel("语速：")
        voice_setting_layout.addWidget(self.speed_label)
        self.speed_label.setFixedSize(82, 20)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        voice_setting_layout.addWidget(self.speed_slider)
        self.speed_slider.setMinimum(20)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setSingleStep(1)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)  # 设置刻度位置
        self.speed_slider.setTickInterval(20)  #
        self.speed_slider.valueChanged.connect(self.speed_change)
        self.speed_slider.setValue(round(GlobalData().voice_speed * 100))

        self.pitch_label = QLabel("变调：")
        voice_setting_layout.addWidget(self.pitch_label)
        self.pitch_label.setFixedSize(82, 20)

        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        voice_setting_layout.addWidget(self.pitch_slider)
        self.pitch_slider.setMinimum(-60)
        self.pitch_slider.setMaximum(60)
        self.pitch_slider.setSingleStep(1)
        self.pitch_slider.setTickPosition(QSlider.TickPosition.TicksBelow)  # 设置刻度位置
        self.pitch_slider.setTickInterval(20) #
        self.pitch_slider.valueChanged.connect(self.pitch_change)
        self.pitch_slider.setValue(round(GlobalData().voice_pitch * 10))
        self.pitch_change(round(GlobalData().voice_pitch * 10))

        self.volume_label = QLabel("音量：")
        self.volume_label.setFixedSize(88, 20)
        voice_setting_layout.addWidget(self.volume_label)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        voice_setting_layout.addWidget(self.volume_slider)
        self.volume_slider.setMinimum(20)
        self.volume_slider.setMaximum(800)
        self.volume_slider.setSingleStep(1)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)  # 设置刻度位置
        self.volume_slider.setTickInterval(20)  #
        self.volume_slider.valueChanged.connect(self.volume_change)
        self.volume_slider.setValue(round(GlobalData().voice_volume * 100))

        #-----------------------------------------------------
        play_layout = QHBoxLayout()
        self.voice_layout.addLayout(play_layout, stretch=1)

        self.save_path = QLineEdit(GlobalData().save_path)
        self.save_path.setReadOnly(True)
        play_layout.addWidget(self.save_path)

        self.voice_path_btn = QPushButton("（2）选取保存路径")
        self.voice_path_btn.clicked.connect(self.set_save_path)
        play_layout.addWidget(self.voice_path_btn)

        self.voice_path = QLineEdit("")
        self.voice_path.setReadOnly(True)
        play_layout.addWidget(self.voice_path)
        self.check_voice_path()

        self.play_voice_btn = QPushButton("播放配音")
        self.play_voice_btn.clicked.connect(self.play_voice)
        play_layout.addWidget(self.play_voice_btn)

        self.reset_voice_btn = QPushButton("重置配音")
        self.reset_voice_btn.clicked.connect(self.reset_voice)
        play_layout.addWidget(self.reset_voice_btn)

        self.del_voice_btn = QPushButton("删除配音")
        self.del_voice_btn.clicked.connect(self.del_voice)
        play_layout.addWidget(self.del_voice_btn)

        self.open_dir_btn = QPushButton("打开目录")

        def _open_dir():
            folder_path = GlobalData().save_path
            open_folder(folder_path)

        self.open_dir_btn.clicked.connect(_open_dir)
        play_layout.addWidget(self.open_dir_btn)

        GenVoice()

        self.check_srt_file()


    def check_voice_path(self):
        if os.path.isfile(GlobalData().voice_path):
            self.voice_path.setText(GlobalData().voice_path)
        else:
            self.voice_path.setText("")

    def check_srt_file(self):
        GlobalData().read_srt_data()
        voice_text_lines.set_list([], 3)
        if GlobalData().srt_data is not None:
            voice_text_lines.set_list([data[2] for data in GlobalData().srt_data], 3)

        ShotData.read_data_from_file()

    def set_voice_text(self):
        if len(ShotData.shot_datas) > 0:
            NoticeManager.add_notice("存在分镜数据，通过分镜修改")
            return

        text = self.novel_edit.toPlainText()
        voice_text_lines.set_list(text.splitlines(), 1)


    def on_voice_line_change(self, dic):
        self.novel_edit.blockSignals(True)
        if dic.get('change_src') != 1:

            text = '\n'.join(voice_text_lines.line_list)
            self.novel_edit.setPlainText(text)

        self.mark_red()

        self.novel_edit.blockSignals(False)


    def gen_text(self):
        new_txt = gen_txt(self.novel_edit.toPlainText(),
                          clear_mark=self.clear_text_mark.checkState() == Qt.CheckState.Checked,
                          remove_chapter=self.remove_chapter_line.checkState() == Qt.CheckState.Checked,
                          tra_num=self.tran_number.checkState() == Qt.CheckState.Checked)

        self.reset_to_default_style()
        self.novel_edit.setPlainText(new_txt)
        self.mark_red()

        self.set_voice_text()

        return new_txt

    def reset_to_default_style(self):
        # 获取文本光标
        cursor = self.novel_edit.textCursor()

        # 全选所有文本
        cursor.select(QTextCursor.SelectionType.Document)

        # 创建默认字符格式并应用
        default_char_format = QTextCharFormat()
        cursor.setCharFormat(default_char_format)

        # 创建默认段落格式并应用
        # default_block_format = QTextBlockFormat()
        # cursor.setBlockFormat(default_block_format)

        # 更新光标和当前格式（确保后续输入也是默认样式）
        self.novel_edit.setTextCursor(cursor)
        self.novel_edit.setCurrentCharFormat(default_char_format)

    def mark_red(self):

        for word in MarkRedData.word_list:
            red_format = QTextCharFormat()
            red_format.setForeground(QColor(220, 20, 60))

            document = self.novel_edit.document()
            cursor = QTextCursor(document)

            cursor.movePosition(QTextCursor.MoveOperation.Start)
            while True:
                cursor = document.find(word, cursor)
                if cursor.isNull():
                    break

                cursor.mergeCharFormat(red_format)
                # cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, len(word))

            document.markContentsDirty(0, document.characterCount())

        self.novel_edit.update()
        self.novel_edit.repaint()



    def open_web(self):
        webbrowser.open("https://www.douyin.com/user/MS4wLjABAAAAjlLSPvg9Z5DknPHKDXbu3VtvaK4Vz9JSF1VoyD--yfI")

    def init_text(self):
        txt_check_box_layout = QHBoxLayout()
        self.frame_layout.addLayout(txt_check_box_layout, stretch=1)

        self.open_web_btn = QPushButton("怎么用？")
        self.open_web_btn.clicked.connect(self.open_web)
        self.open_web_btn.setStyleSheet(web_btn_css)

        self.clear_text_mark = QCheckBox("去除标点符号")
        self.clear_text_mark.setCheckState(Qt.CheckState.Unchecked)
        self.remove_chapter_line = QCheckBox("去除章节行")
        self.remove_chapter_line.setCheckState(Qt.CheckState.Checked)
        self.tran_number = QCheckBox("数字转中文")
        self.tran_number.setCheckState(Qt.CheckState.Checked)

        txt_check_box_layout.addWidget(self.open_web_btn)
        txt_check_box_layout.addWidget(self.clear_text_mark)
        txt_check_box_layout.addWidget(self.remove_chapter_line)
        txt_check_box_layout.addWidget(self.tran_number)


        self.replace_word_btn = QPushButton("词替换")
        self.replace_word_btn.clicked.connect(self.open_replace_view)
        txt_check_box_layout.addWidget(self.replace_word_btn)

        self.mark_red_btn = QPushButton("标红")
        self.mark_red_btn.clicked.connect(self.open_red_mark_view)
        txt_check_box_layout.addWidget(self.mark_red_btn)

        self.gen_text_btn = QPushButton("整理全文")
        self.gen_text_btn.clicked.connect(self.gen_text)
        txt_check_box_layout.addWidget(self.gen_text_btn)

        # 创建文本编辑框
        self.novel_edit = QTextEdit("（1）复制小说到这里")
        self.cursor = self.novel_edit.textCursor()
        self.frame_layout.addWidget(self.novel_edit, stretch=15)

        self.novel_edit.textChanged.connect(self.set_voice_text)
        voice_text_lines.data_change.connect(self.on_voice_line_change)

    def init_ui(self):
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(3)
        self.frame_layout = QVBoxLayout()
        self.setLayout(self.frame_layout)

        self.init_text()
        self.init_voice()

    # def login_web(self):
    #     img_path = self.text_to_voice.get_login_qrcode()
    #     if not self.login_msg_box:
    #         self.login_msg_box = QrcodeNotice(self, img_path)
    #     else:
    #         self.login_msg_box.change_img(img_path)
    #         self.login_msg_box.show()
    #
    #     @pyqtSlot(dict)
    #     def close_msg_box(data):
    #         self.login_msg_box.close()
    #         self.text_to_voice.set_login_data(data)
    #         self.login_thread.stop()
    #         NoticeManager.add_notice("登陆完成")
    #
    #     if not self.login_thread:
    #         self.login_thread = WaitLoginThread(self.login_msg_box, self.text_to_voice.login_uuid)
    #         self.login_thread.finished.connect(close_msg_box)
    #
    #     self.login_thread.running = True
    #     self.login_thread.start()
    #     self.login_msg_box.set_close_cb(self.login_thread.stop)



    def set_clip_txt_color(self, pos, size, color):
        char_format = QTextCharFormat()
        char_format.setFontWeight(QFont.Weight.Bold)  # 设置为粗体
        char_format.setForeground(color)

        self.cursor.setPosition(pos)
        self.cursor.mergeCharFormat(char_format)
        self.cursor.setPosition(pos + size, QTextCursor.MoveMode.KeepAnchor)
        self.cursor.mergeCharFormat(char_format)

    def run_clip_txt_anime(self, idx, pos, size):
        if len(self.anime_timers) <= idx:
            self.anime_timers.insert(idx, (QTimer(self), [pos, size]))
        else:
            self.anime_timers[idx][1][:] = pos, size

        color_list = [QColor("#5D4037"), QColor("#795548"), QColor("#4A4A4A"), QColor("#1976D2")]

        def time_out():
            self.set_clip_txt_color(pos, size, color_list[random.randint(0, 3)])

        try:
            self.anime_timers[idx][0].timeout.disconnect()
        except TypeError:
            pass

        self.anime_timers[idx][0].timeout.connect(time_out)
        self.anime_timers[idx][0].start(500)

    def stop_clip_txt_anime(self):
        [timer[0].stop() for timer in self.anime_timers]

    # @pyqtSlot(dict)
    # def req_voice_finnished(self, dic_data):
    #
    #     if dic_data.get('need_login'):
    #         self.thread_pool.clear()
    #         NoticeManager.add_notice("登录失效")
    #         self.stop_clip_txt_anime()
    #         self.login_web()
    #         return
    #
    #     if dic_data.get('sucess'):
    #         idx = dic_data['idx']
    #
    #         self.set_clip_txt_color(idx * self.max_req_size, dic_data['size'], QColor(60, 179, 113))
    #         self.anime_timers[idx].stop()
    #     else:
    #         NoticeManager.add_notice(dic_data.get('msg'))

    def connect_jian_ying_voice(self, call_back=None):
        jian_ying_clip_path = self.jian_ying_draft_path.text()


        if jian_ying_clip_path:
            self.gen_finnal_voice(call_back=call_back, jianying_clip_path=jian_ying_clip_path)
        else:
            NoticeManager.add_notice("请先设定草稿文件夹")

    def gen_finnal_voice(self, new_setting=None, call_back=None, jianying_clip_path=None):
        out_path = GlobalData().voice_path

        self.stop_play_voice()

        delete_file(out_path)
        self.check_voice_path()

        new_setting = new_setting if new_setting is not None else GlobalData().get_voice_setting()

        def refresh_progress(msg):
            if 'value' in msg:
                desc = "配音片段拼接中"
                if 'rename' in msg:
                    desc = "逆向翻译剪映配音"

                if 'loading' in msg:
                    desc = "正在加载逆向模型"

                self.parent().set_progress_bar(msg['value'], msg['total_value'], desc)
            elif 'error' in msg:
                self.parent().gen_progress_error(msg['error'])
                self.setEnabled(True)
            elif 'end' in msg:
                self.check_voice_path()
                self.cur_setting = new_setting

                self.parent().set_progress_bar(1, 1, "配音生成完成")

                if call_back:
                    call_back()

                NoticeManager.add_notice("配音生成完成")

                self.setEnabled(True)

        self.setEnabled(False)

        self.aot = AudioOpThread(jianying_clip_path)
        self.aot.signals.finished.connect(refresh_progress)
        self.aot.start_connect_voice_thread(GlobalData().voice_clip_path,
                                out_path,
                                GlobalData().srt_path,
                                voice_text_lines.line_list,
                                **new_setting)


    @pyqtSlot(dict)
    def gen_voice_finnished(self, dic_data):
        if dic_data.get('sucess'):
            idx = dic_data['idx']

            timer_data = self.anime_timers[idx]
            timer_data[0].stop()
            self.set_clip_txt_color(timer_data[1][0], timer_data[1][1], QColor(60, 179, 113))
        else:
            NoticeManager.add_notice(dic_data.get('msg'))

        self.task_finish += 1

        self.novel_edit.moveCursor(QTextCursor.MoveOperation.Down)

        if self.task_finish == self.task_num:
            self.setEnabled(True)

            self.gen_finnal_voice(call_back=self.gen_voice_cb)


    def gen_clone_voice(self, finish_cb=None, err_cb=None):
        if GlobalData().voice_clone_path is None:
            NoticeManager.add_notice("请先选取想要克隆的声音")
            return

        if VoiceClone.device is None:
            NoticeManager.add_notice("克隆模型还在加载，请稍后再试。")
            if err_cb:
                err_cb()
            return

        VoiceClone.save_path = GlobalData().voice_clip_path

        if VoiceClone.voice_clone_path != GlobalData().voice_clone_path:
            VoiceClone.voice_clone_path = GlobalData().voice_clone_path
            VoiceClone.prompt_tokenize(VoiceClone.voice_clone_path)

        self.thread_pool.clear()
        self.stop_clip_txt_anime()
        self.gen_text()

        clip_path = GlobalData().voice_clip_path
        delete_files_in_folder(clip_path)
        os.makedirs(clip_path, exist_ok=True)

        text = self.novel_edit.toPlainText()
        self.novel_edit.moveCursor(QTextCursor.MoveOperation.Start)

        if len(text) <= 0:
            NoticeManager.add_notice("未输入小说内容")
            return

        self.setEnabled(False)
        self.gen_voice_cb = finish_cb
        pos = 0
        line_list = text.splitlines()
        self.task_finish = 0
        self.task_num = len(line_list)
        for idx, line in enumerate(line_list):
            rv_task = GenVoiceCloneTask(line, idx)
            rv_task.signals.finished.connect(self.gen_voice_finnished)
            self.thread_pool.start(rv_task)
            size = len(line)
            self.run_clip_txt_anime(idx, pos, size)

            pos += size + 1


    def gen_voice(self, finish_cb=None, err_cb=None):
        GenVoice()._save_path = GlobalData().voice_clip_path
        if not GenVoice().pipelines:
            NoticeManager.add_notice("配音模型还在加载，请稍后再试。")
            if err_cb:
                err_cb()
            return

        self.thread_pool.clear()
        self.stop_clip_txt_anime()
        self.gen_text()

        clip_path = GlobalData().voice_clip_path
        delete_files_in_folder(clip_path)
        os.makedirs(clip_path, exist_ok=True)

        text = self.novel_edit.toPlainText()
        self.novel_edit.moveCursor(QTextCursor.MoveOperation.Start)

        if len(text) <= 0:
            NoticeManager.add_notice("未输入小说内容")
            return

        self.setEnabled(False)
        self.gen_voice_cb = finish_cb
        pos = 0
        line_list = text.splitlines()
        self.task_finish = 0
        self.task_num = len(line_list)
        for idx, line in enumerate(line_list):
            rv_task = GenVoiceTask(line, self.sel_voice_name, float(self.voice_speed), idx)
            rv_task.signals.finished.connect(self.gen_voice_finnished)
            self.thread_pool.start(rv_task)
            size = len(line)
            self.run_clip_txt_anime(idx, pos, size)

            pos += size + 1

    def open_replace_view(self):
        if self.replace_window is None:
            self.replace_window = ReplaceWindow()

        self.replace_window.show()

    def open_red_mark_view(self):
        if self.mark_red_window is None:
            self.mark_red_window = MarkRedWindow()

        self.mark_red_window.show()

    def release(self):
        self.thread_pool.clear()
        if self.jian_ying_op_thread:
            self.jian_ying_op_thread.quit()
            self.jian_ying_op_thread.wait()
