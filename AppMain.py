
import os.path
import sys
import time
import traceback

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QProgressBar, QLabel, \
    QCheckBox

from GlobalData import GlobalData
from LeftFrame import LeftFrame
from MyLog import MyLog
from NoticeManager import NoticeManager
from QtLayoutCss import layout_css_str
from RightFrame import RightFrame
from Setting import Setting
from ShotData import ShotData
from VideoWrite import VideoWrite
from VoiceText import voice_text_lines


class AppMainWindow(QWidget):
    finished = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.gv_thread = None

    def init_ui(self):
        # 设置窗口属性
        self.setWindowTitle("合成配音填充视频字幕")
        self.resize(1660, 800)  # 设置窗口大小

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.setStyleSheet(layout_css_str)

        NoticeManager(self)
        frame_layout = QHBoxLayout()
        self.main_layout.addLayout(frame_layout)

        self.left_frame = LeftFrame(self)
        frame_layout.addWidget(self.left_frame, stretch=1)

        self.right_frame = RightFrame(self)
        frame_layout.addWidget(self.right_frame, stretch=1)

        out_put_layout = QHBoxLayout()
        self.main_layout.addLayout(out_put_layout)

        self.attach_srt = QCheckBox("附加字幕")
        self.attach_srt.stateChanged.connect(self.attach_change)
        self.attach_srt.setCheckState(Qt.CheckState.Checked)
        out_put_layout.addWidget(self.attach_srt, stretch=1)

        self.gen_video_btn = QPushButton("（5）自动填充视频和背景音乐长度输出视频")
        self.gen_video_btn.clicked.connect(self.gen_video)
        out_put_layout.addWidget(self.gen_video_btn, stretch=20)

        self.gen_video_progress_bar = QProgressBar(self)
        self.main_layout.addWidget(self.gen_video_progress_bar)

        self.progress_lab = QLabel("按1-5步骤处理即可", self.gen_video_progress_bar)
        self.progress_lab.setFixedSize(200, 20)
        self.progress_lab.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.progress_lab.move(400, 2)

        # test_rub = test_rub_on_thread('test.wav')

    def attach_change(self):
        GlobalData().attach_srt = self.attach_srt.checkState()

    def set_progress_bar(self, value, total_value, desc):
        self.progress_lab.setText(desc)

        self.gen_video_progress_bar.setMaximum(total_value)
        self.gen_video_progress_bar.setValue(value)

    def gen_progress_error(self, error=None):
        self.setEnabled(True)
        if error:
            NoticeManager.add_notice(error)

    def refresh_gen_progress_bar(self, dict):
        if 'end' in dict:
            self.showNormal()
            self.end_time = time.time()
            self.setEnabled(True)

            #{self.end_time - self.start_time}

            self.set_progress_bar(1, 1, f"生成完成")

        elif 'error' in dict:
            self.gen_progress_error(dict.get('error'))
        elif 'value' in dict:
            desc = ''
            if dict.get('finnal_packaging'):
                desc = '正在整合视频'

            self.set_progress_bar(dict['value'], dict['total_value'], desc)

    def gen_video(self):
        self.setEnabled(False)

        Setting.reload_setting()

        self.right_frame.gl_window.clear_shader_queue()

        if not os.path.isfile(GlobalData().voice_path):
            gen_voice_tab = self.left_frame.voice_tab_widget.currentIndex()

            if gen_voice_tab == 1:
                NoticeManager.add_notice("开始生成配音")
                self.left_frame.gen_voice(self.gen_video, self.gen_progress_error)
                return
            elif gen_voice_tab == 2:
                NoticeManager.add_notice("开始生成克隆配音")
                self.left_frame.gen_clone_voice(self.gen_video, self.gen_progress_error)
                return
            else:
                if self.left_frame.jian_ying_auto_model:
                    NoticeManager.add_notice("开始自动生成剪映配音")
                    self.left_frame.gen_jian_ying_voice(self.gen_video, self.gen_progress_error)
                    return
                else:
                    NoticeManager.add_notice("选择了手动模式，却还未生成剪映配音")
                    self.setEnabled(True)
                    return


        if len(ShotData.shot_datas) <= 0:
            if GlobalData().video_paths is None:
                NoticeManager.add_notice("未选取混剪视频或图片")
                self.setEnabled(True)
                return
        else:
            GlobalData().read_srt_data()

            if len(GlobalData().srt_data) != len(voice_text_lines.line_list):
                NoticeManager.add_notice("文本与配音不匹配， 修改文本需重新配音")
                self.setEnabled(True)
                return

            for shot_data in ShotData.shot_datas:
                if shot_data.img_path is None:
                    NoticeManager.add_notice("存在未分配画面，请先行分配")
                    self.setEnabled(True)
                    return

        self.left_frame.voice_tab_widget.setCurrentIndex(0)

        vw = VideoWrite(self)
        vw.signals.finished.connect(self.refresh_gen_progress_bar)
        vw.start_write_thread()

    def closeEvent(self, event):
        self.finished.emit(True)


if __name__ == "__main__":
    # 创建应用程序实例
    app = QApplication(sys.argv)

    # 创建主窗口实例
    ex = AppMainWindow()

    # 显示窗口
    ex.show()

    def exception_hook(exc_type, exc_value, exc_traceback):
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        if Setting.get('debug'):
            # 格式化错误信息
            print(f"ERROR DETAILS:\n{error_msg}")  # 可替换为日志记录

            # 可选：记录局部变量（需结合 inspect 模块）
            # sys.__excepthook__(exc_type, exc_value, exc_traceback)  # 保留默认行为

        NoticeManager.add_notice(error_msg)



    sys.excepthook = exception_hook

    # 启动事件循环
    sys.exit(app.exec())