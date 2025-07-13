layout_css_str = """
    QFrame {
        border: 1px solid dimgray; 
        border-radius: 10px; 
        background-color: darkgray;
    }
    QFrame[red_mode="true"]{
        background-color: #ffcccc;
    }
    QWidget {
        background-color: #f0f0f0; /* 浅灰色背景 */
        font-family: Arial, sans-serif;
    }
    QTextEdit {
        background-color: white; /* 白色背景 */
        border: 1px solid #ccc; /* 浅灰色边框 */
        border-radius: 5px; /* 圆角边框 */
        padding: 5px; /* 内边距 */
        font-size: 14px;
    }
    QCheckBox {
        font-size: 14px;
        color: #333; /* 深灰色文本 */
    }
    QPushButton {
        background-color: #4CAF50; /* 绿色背景 */
        color: white; /* 白色文本 */
        border: none;
        border-radius: 5px; /* 圆角边框 */
        padding: 10px 20px; /* 内边距 */
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #45a049; /* 鼠标悬停时的背景颜色 */
    }
    QPushButton:disabled {
        background-color: rgb(230,0,0); /* 不可点击时的背景颜色 */
    }
    QLabel {
        font-size: 16px;
        color: #333; /* 深灰色文本 */
        border-radius: 2px;
        border: none;
    }
    QComboBox {
        background-color: #fff; /* 背景颜色 */
        color: #333; /* 字体颜色 */
        border: 1px solid #ccc; /* 边框颜色 */
        border-radius: 5px; /* 边框圆角 */
        padding: 5px; /* 内边距 */
        font-size: 16px; /* 字体大小 */
    }
    QComboBox QAbstractItemView {
        background-color: #fff; /* 下拉菜单的背景颜色 */
        border: 1px solid #ccc; /* 下拉菜单的边框颜色 */
        selection-background-color: #0078d7; /* 选中项的背景颜色 */
        selection-color: white; /* 选中项的字体颜色 */
    }
    QLineEdit {
        background-color: #f0f0f0;  /* 背景颜色 */
        border: 2px solid #ccc;     /* 边框颜色和宽度 */
        border-radius: 2px;        /* 边框圆角 */
        padding: 2px;               /* 内边距 */
        font-size: 16px;            /* 字体大小 */
        color: #333;                /* 字体颜色 */
    }
    QLineEdit:focus {
        border-color: #0078d7;      /* 聚焦时的边框颜色 */
        background-color: #ffffff;  /* 聚焦时的背景颜色 */
    }
    QTabWidget {
        background-color: #f5f5f5;
    }
    
    QTabBar {
        background-color: #f0f0f0;
        border-bottom: 1px solid #d7d7d7;
        font-size: 14px;
        font-weight: bold;
    }
    
    QTabBar::tab {
        background-color: #c8c8c8;
        border: 1px solid #d7d7d7;
        border-bottom: none;
        min-width: 90px;
        height: 30px;
        padding: 5px 10px;
        margin-right: 6px;
    }
    
    QTabBar::tab:hover {
        background-color: #e0e0e0;
    }
    
    QTabBar::tab:selected {
        background-color: white;
        border-color: #a0a0a0 #a0a0a0 #d7d7d7 #a0a0a0;
        border-bottom: none;
    }
    
    QTabWidget::tab-bar {
        alignment: left;
    }
    
    QTabWidget::pane {
        background-color: #f0f0f0;
    }
    
    QTabBar::tab:first:selected {
        border-top-left-radius: 5px;
    }
    
    QTabBar::tab:last:selected {
        border-top-right-radius: 5px;
    }
    
    QTabBar::tab:only-one {
        margin-right: 0;
    }
"""

msg_css_str = """
    QLabel {
        font-size: 24px;
        color: white;
        background-color: rgba(0, 0, 0, 60);
        border-radius: 0px;
    }
"""

web_btn_css = """
QPushButton {
    background-color: #FFA726;  /* 柔和的南瓜橙色 */
    border: 1px solid #FF8F00;  /* 稍深的橙色边框 */
    border-radius: 8px;         /* 圆角半径 */
    padding: 8px 16px;          /* 内边距 */
    color: white;               /* 文字颜色 */
    font-weight: bold;          /* 粗体字 */
}

QPushButton:hover {
    background-color: #FFB74D;  /* 悬停时稍亮的橙色 */
    border: 1px solid #FF6D00;  /* 更明显的边框 */
}

QPushButton:pressed {
    background-color: #FF9100;  /* 按下时更深的橙色 */
    border: 1px solid #FF6D00;
}

QPushButton:focus {
    outline: none;             /* 移除默认的蓝色焦点框 */
}
"""

qrcode_css_str = """
    QLabel {
        font-size: 30px;
        color: red;
        background-color: rgba(0, 0, 0, 200);
        border-radius: 0px;
    }
"""