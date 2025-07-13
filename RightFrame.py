import os

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QFileDialog, QPushButton, QLabel, QHBoxLayout, QCheckBox, QComboBox, \
    QLineEdit, QSlider

from AudioOpThread import AudioOpThread
from FaceMeshManage import FaceMeshManage
from GlobalData import GlobalData
from GLWidget import GLWidget
from NoticeManager import NoticeManager
from VideoEditorWindow import VideoEditorWindow


class RightFrame(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()

        self.cur_bgm = None
        self.video_editor = None

    def replace_face_sel(self):
        self.face_img_path, _ = QFileDialog.getOpenFileName(self, caption='选取替换人脸',
                                                       filter="Images (*.png *.jpg)")
        if self.face_img_path:
            fmm = FaceMeshManage(self.face_img_path)
            if fmm.src_pts is None:
                self.face_img_lab.setText("图片识别不到人脸")
                NoticeManager.add_notice("图片识别不到人脸")
                GlobalData().replace_face_manage = None
            else:
                NoticeManager.add_notice("人脸识别完成")
                self.face_img_lab.setText("人脸识别完成")
                GlobalData().replace_face_manage = fmm
        else:
            GlobalData().replace_face_manage = None
            self.face_img_lab.setText("不使用换脸")

        self.eff_change()


    def sel_video(self):
        video_paths, _ = QFileDialog.getOpenFileNames(self, caption='选取多个视频', filter="*.mp4")
        if video_paths:
            self.videos_lab.setText(f"{[os.path.basename(file) for file in video_paths]}")
            GlobalData().video_paths = video_paths
            self.gl_window.refresh_gl()

    def sel_bgm(self):
        self.bgm_path, _ = QFileDialog.getOpenFileName(self, caption='选取全局背景音', filter="Audio Files (*.mp3 *.wav)")
        if self.bgm_path:
            GlobalData().bgm_path = self.bgm_path
            self.bgm_lab.setText(self.bgm_path)

    def resolution_changed(self, idx):
        if idx == 0:
            GlobalData().video_resolution = None
        elif idx == 1:
            GlobalData().video_resolution = 4 / 3
        elif idx == 2:
            GlobalData().video_resolution = 9 / 16


    def volume_change(self, value):
        self.bgm_volume = value * 0.01
        GlobalData().bgm_volume = self.bgm_volume
        self.bgm_volume_lab.setText(f'音量:{self.bgm_volume:.2f}')

    def pitch_change(self, value):
        self.bgm_pitch = value * 0.1
        GlobalData().bgm_pitch = self.bgm_pitch
        self.bgm_pitch_lab.setText(f'变调:{self.bgm_pitch:.2f}')

    def speed_change(self, value):
        self.bgm_speed = value * 0.01
        GlobalData().bgm_speed = self.bgm_speed
        self.bgm_speed_lab.setText(f'速度:{self.bgm_speed:.2f}')

    def eff_change(self):
        GlobalData().eff_dict = {}
        GlobalData().eff_dict['suiping'] = self.suiping_eff.checkState() == Qt.CheckState.Checked
        GlobalData().eff_dict['wutaidengguang'] = self.wutaidengguang_eff.checkState() == Qt.CheckState.Checked
        GlobalData().eff_dict['crtpingmu'] = self.crtpingmu_eff.checkState() == Qt.CheckState.Checked
        GlobalData().eff_dict['zaoyin'] = self.zaoyin_eff.checkState() == Qt.CheckState.Checked
        # GlobalData().eff_dict['xuancai'] = self.xuancai_eff.checkState()
        # GlobalData().eff_dict['liuxing'] = self.liuxing_eff.checkState()
        GlobalData().eff_dict['baoguang'] = self.baoguang_eff.checkState() == Qt.CheckState.Checked
        GlobalData().eff_dict['niuqu'] = self.niuqu_eff.checkState() == Qt.CheckState.Checked
        GlobalData().eff_dict['heidong'] = self.heidong_eff.checkState() == Qt.CheckState.Checked
        GlobalData().eff_dict['face_replace'] = GlobalData().replace_face_manage is not None

        self.gl_window.refresh_gl()

    def play_bgm(self):
        if not GlobalData().bgm_path:
            NoticeManager.add_notice("没选bgm，播个der")
            return

        if not self.media_play:
            self.media_play = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_play.setAudioOutput(self.audio_output)

        self.media_play.stop()
        self.media_play.setSource(QUrl())

        def refresh_progress(dict):
            if 'value' in dict:
                self.parent().set_progress_bar(dict['value'], dict['total_value'], "背景音调整中")
            elif 'error' in dict:
                self.parent().gen_progress_error(dict['error'])
            elif 'end' in dict:
                GlobalData().bgm_setting = new_setting
                NoticeManager.add_notice("背景音调整完成")
                self.play_bgm()

        new_setting = {'volume':GlobalData().bgm_volume, 'pitch':GlobalData().bgm_pitch, 'speed':GlobalData().bgm_speed}
        if GlobalData().bgm_setting != new_setting or self.cur_bgm != GlobalData().bgm_path:
            aot = AudioOpThread()
            aot.signals.finished.connect(refresh_progress)
            aot.start_variation_audio_thread(GlobalData().bgm_path, GlobalData().temp_bgm, **new_setting)
            NoticeManager.add_notice("背景音设置变更开始调整音频")
            self.cur_bgm = GlobalData().bgm_path
            return


        # self.media_play.setMedia(QMediaContent())

        self.media_play.setSource(QUrl.fromLocalFile(GlobalData().temp_bgm))

        # self.media_play.setMedia(QMediaContent(QUrl.fromLocalFile(GlobalData().temp_bgm)))
        self.media_play.play()

    def init_ui(self):
        self.vd_frame_layout = QVBoxLayout()
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(3)
        self.setLayout(self.vd_frame_layout)

        sel_bgm_layout = QHBoxLayout()
        self.vd_frame_layout.addLayout(sel_bgm_layout, stretch=1)

        self.bgm_lab = QLineEdit('尚未选取背景音乐。')
        self.bgm_lab.setReadOnly(True)
        self.bgm_lab.setFixedSize(180, 28)
        sel_bgm_layout.addWidget(self.bgm_lab)

        self.browse_bgm_btn = QPushButton("（3）选取全局背景音乐")
        self.browse_bgm_btn.clicked.connect(self.sel_bgm)
        sel_bgm_layout.addWidget(self.browse_bgm_btn)

        self.bgm_volume_lab = QLabel("音量:")
        self.bgm_volume_lab.setFixedSize(76, 20)
        sel_bgm_layout.addWidget(self.bgm_volume_lab)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        sel_bgm_layout.addWidget(self.volume_slider)
        self.volume_slider.setMinimum(10)
        self.volume_slider.setMaximum(200)
        self.volume_slider.setSingleStep(1)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)  # 设置刻度位置
        self.volume_slider.setTickInterval(10)  #
        self.volume_slider.valueChanged.connect(self.volume_change)
        self.volume_slider.setValue(round(GlobalData().bgm_volume * 100) )

        self.bgm_pitch_lab = QLabel('变调：')
        self.bgm_pitch_lab.setFixedSize(76, 20)
        sel_bgm_layout.addWidget(self.bgm_pitch_lab)

        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        sel_bgm_layout.addWidget(self.pitch_slider)
        self.pitch_slider.setToolTip('变调会改变音质慎用')
        self.pitch_slider.setToolTipDuration(0)
        self.pitch_slider.setMinimum(-60)
        self.pitch_slider.setMaximum(60)
        self.pitch_slider.setSingleStep(1)
        self.pitch_slider.setTickPosition(QSlider.TickPosition.TicksBelow)  # 设置刻度位置
        self.pitch_slider.setTickInterval(20)  #
        self.pitch_slider.valueChanged.connect(self.pitch_change)
        self.pitch_slider.setValue(round(GlobalData().bgm_pitch * 10))
        self.pitch_change(round(GlobalData().bgm_pitch * 10))

        self.bgm_speed_lab = QLabel('变速：')
        self.bgm_speed_lab.setFixedSize(76, 20)
        sel_bgm_layout.addWidget(self.bgm_speed_lab)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        sel_bgm_layout.addWidget(self.speed_slider)
        self.speed_slider.setToolTip('变奏会改变音质慎用')
        self.speed_slider.setToolTipDuration(0)
        self.speed_slider.setMinimum(20)
        self.speed_slider.setMaximum(400)
        self.speed_slider.setSingleStep(1)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)  # 设置刻度位置
        self.speed_slider.setTickInterval(40)  #
        self.speed_slider.valueChanged.connect(self.speed_change)
        self.speed_slider.setValue(round(GlobalData().bgm_speed * 100))

        self.play_btn = QPushButton("播放")
        sel_bgm_layout.addWidget(self.play_btn)
        self.play_btn.clicked.connect(self.play_bgm)
        self.media_play = None

        self.gl_window = GLWidget()
        self.vd_frame_layout.addWidget(self.gl_window, stretch=15)

        self.video_frame = QFrame()
        video_set_layout = QVBoxLayout()
        self.vd_frame_layout.addWidget(self.video_frame, stretch=2)
        self.video_frame.setLayout(video_set_layout)

        check_video_eff_layout = QHBoxLayout()
        video_set_layout.addLayout(check_video_eff_layout)

        check_video_eff_layout.addWidget(QLabel('不勾选,只将视频随机拼接'))

        self.face_img_lab = QLineEdit('不使用换脸')
        self.face_img_lab.setReadOnly(True)
        self.face_img_lab.setFixedSize(180, 28)
        check_video_eff_layout.addWidget(self.face_img_lab)

        self.replace_face_sel_btn = QPushButton("丐版换脸")
        self.replace_face_sel_btn.clicked.connect(self.replace_face_sel)
        check_video_eff_layout.addWidget(self.replace_face_sel_btn)

        self.suiping_eff = QCheckBox("碎屏")
        self.suiping_eff.stateChanged.connect(self.eff_change)
        self.suiping_eff.setCheckState(Qt.CheckState.Unchecked)
        check_video_eff_layout.addWidget(self.suiping_eff)

        self.wutaidengguang_eff = QCheckBox("舞台")
        self.wutaidengguang_eff.stateChanged.connect(self.eff_change)
        self.wutaidengguang_eff.setCheckState(Qt.CheckState.Unchecked)
        check_video_eff_layout.addWidget(self.wutaidengguang_eff)

        self.niuqu_eff = QCheckBox("扭曲")
        self.niuqu_eff.stateChanged.connect(self.eff_change)
        self.niuqu_eff.setCheckState(Qt.CheckState.Unchecked)
        check_video_eff_layout.addWidget(self.niuqu_eff)

        self.crtpingmu_eff = QCheckBox("crt屏")
        self.crtpingmu_eff.stateChanged.connect(self.eff_change)
        self.crtpingmu_eff.setCheckState(Qt.CheckState.Unchecked)
        check_video_eff_layout.addWidget(self.crtpingmu_eff)

        self.zaoyin_eff = QCheckBox("噪音")
        self.zaoyin_eff.stateChanged.connect(self.eff_change)
        self.zaoyin_eff.setCheckState(Qt.CheckState.Unchecked)
        check_video_eff_layout.addWidget(self.zaoyin_eff)

        # self.xuancai_eff = QCheckBox("炫彩")
        # self.xuancai_eff.stateChanged.connect(self.eff_change)
        # self.xuancai_eff.setCheckState(Qt.Unchecked)
        # check_video_eff_layout.addWidget(self.xuancai_eff)

        self.baoguang_eff = QCheckBox("曝光")
        self.baoguang_eff.stateChanged.connect(self.eff_change)
        self.baoguang_eff.setCheckState(Qt.CheckState.Unchecked)
        check_video_eff_layout.addWidget(self.baoguang_eff)

        # self.liuxing_eff = QCheckBox("流星")
        # self.liuxing_eff.stateChanged.connect(self.eff_change)
        # self.liuxing_eff.setCheckState(Qt.Unchecked)
        # check_video_eff_layout.addWidget(self.liuxing_eff)

        self.heidong_eff = QCheckBox("黑洞")
        self.heidong_eff.stateChanged.connect(self.eff_change)
        self.heidong_eff.setCheckState(Qt.CheckState.Unchecked)
        check_video_eff_layout.addWidget(self.heidong_eff)

        sel_video_layout = QHBoxLayout()
        video_set_layout.addLayout(sel_video_layout)

        sel_video_layout.addWidget(QLabel('画面比例'))

        self.resolution_comb = QComboBox()
        self.resolution_comb.addItem('原比例')
        self.resolution_comb.addItem('4:3')
        self.resolution_comb.addItem('9:16')
        self.resolution_comb.currentIndexChanged.connect(self.resolution_changed)
        sel_video_layout.addWidget(self.resolution_comb)

        self.videos_lab = QLineEdit('尚未选取视频')
        sel_video_layout.addWidget(self.videos_lab)

        self.browse_video_btn = QPushButton("（4）选取混剪视频")
        self.browse_video_btn.clicked.connect(self.sel_video)
        sel_video_layout.addWidget(self.browse_video_btn)


        self.video_editor_btn = QPushButton("(4)分镜编辑")
        self.video_editor_btn.clicked.connect(self.open_video_editor)
        sel_video_layout.addWidget(self.video_editor_btn)

    def open_video_editor(self):
        if self.video_editor is None:
            self.video_editor = VideoEditorWindow()
        else:
            self.video_editor.refresh_items()

        self.video_editor.show()