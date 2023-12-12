# Third-party libraries
from loguru import logger
from PySide6.QtCore import Signal, Qt, QRect
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QCheckBox, QDialog, QFontDialog, QHBoxLayout,
                               QLabel, QPlainTextEdit, QPushButton, QSizePolicy,
                               QSpacerItem, QVBoxLayout)

# Sources
from src.config.config import load_config, update_config
from src.ui.asset_manager import app_icon


class OCRTextUI(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyTextractOCR - OCR Text")
        self.setWindowIcon(QIcon(app_icon))
        self.setGeometry(0, 0, 500, 300)  # Initial dialog size
        self.setMinimumSize(300, 200)

        self.config = None
        self.initial_font = None
        self.pos_x = None
        self.pos_y = None
        self.text_edit_extracted = None
        self.text_edit_translated = None
        self.checkbox_always_on_top = None
        self.clickable_label_font = None
        self.button_ok = None
        self.horizontal_bottom_layout = None

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.setContentsMargins(5, 5, 5, 5)

    def init_ui(self):
        # Clear existing layout
        if hasattr(self, 'vertical_layout'):
            while self.vertical_layout.count():
                child = self.vertical_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        self.config = load_config()
        self.load_popup_window_position()
        self.load_font_config()

        self.text_edit_extracted = QPlainTextEdit(self)
        self.text_edit_extracted.setFont(self.initial_font)
        self.text_edit_extracted.setPlainText("")
        self.vertical_layout.addWidget(self.text_edit_extracted)

        # Add new QPlainTextEdit if translation is enabled
        if self.config['translate']['enable_translation']:
            self.text_edit_translated = QPlainTextEdit(self)
            self.text_edit_translated.setFont(self.initial_font)
            self.text_edit_translated.setPlainText("")
            self.vertical_layout.addWidget(self.text_edit_translated)
        else:
            self.text_edit_translated = None

        self.horizontal_bottom_layout = QHBoxLayout()

        widgets = {
            'checkbox_always_on_top': self.checkbox_always_on_top,
            'clickable_label_font': self.clickable_label_font,
            'button_ok': self.button_ok
        }
        for widget_name, widget in widgets.items():
            if widget:
                self.horizontal_bottom_layout.removeWidget(widget)
                widget.deleteLater()
                setattr(self, widget_name, None)

        self.checkbox_always_on_top = QCheckBox("Always on top", self)
        self.checkbox_always_on_top.setGeometry(QRect(16, 110, 190, 20))
        if self.config['ocr_window']['always_on_top']:
            self.checkbox_always_on_top.setChecked(True)
            self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.checkbox_always_on_top.stateChanged.connect(self.set_always_on_top)
        self.horizontal_bottom_layout.addWidget(self.checkbox_always_on_top)

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontal_bottom_layout.addItem(spacer)

        # ClickableLabel for changing the font
        self.clickable_label_font = ClickableLabel("Font", self)
        self.clickable_label_font.setStyleSheet("color: blue; text-decoration: underline;")
        self.clickable_label_font.setToolTip("<html><head/><body><p style='color: rgb(87, 87, 87);"
                                             "text-decoration: none;'>Customize text font</p></body></html>")
        self.clickable_label_font.clicked.connect(self.change_font)
        self.horizontal_bottom_layout.addWidget(self.clickable_label_font)

        self.button_ok = QPushButton("OK", self)
        self.button_ok.setFixedSize(75, 23)
        self.button_ok.setAutoDefault(False)
        self.button_ok.setToolTip("Close window and save window position")
        self.horizontal_bottom_layout.addWidget(self.button_ok)
        self.button_ok.clicked.connect(self.ok_button_clicked)

        self.vertical_layout.addLayout(self.horizontal_bottom_layout)
        self.setLayout(self.vertical_layout)

    def set_extracted_text(self, text):
        self.text_edit_extracted.setPlainText(text)

    def set_translated_text(self, text):
        self.text_edit_translated.setPlainText(text)

    def save_popup_window_position(self):
        window_position_x = self.pos().x()
        window_position_y = self.pos().y()
        self_pos_xy = {
            "ocr_window": {
                'position_x': window_position_x,
                'position_y': window_position_y
            }
        }
        logger.info(f"OCR Text window saved position: X: {window_position_x} Y: {window_position_y}")
        update_config(self_pos_xy)

    def load_popup_window_position(self):
        self.pos_x = self.config['ocr_window']['position_x']
        self.pos_y = self.config['ocr_window']['position_y']
        self.move(self.pos_x, self.pos_y)

    def load_font_config(self):
        initial_font_name = self.config['ocr_window']['font_name']
        initial_font_size = self.config['ocr_window']['font_size']
        initial_font_weight = self.config['ocr_window']['font_weight']
        initial_font_strikeout = self.config['ocr_window']['font_strikeout']
        initial_font_underline = self.config['ocr_window']['font_underline']

        # Set the fourth parameter to True if italic or bold is in Font Style
        initial_font_style = self.config['ocr_window']['font_style']
        initial_font_italic = True if 'italic' in initial_font_style.lower() else False
        initial_font_bold = True if 'bold' in initial_font_style.lower() else False

        self.initial_font = QFont(initial_font_name, initial_font_size, initial_font_weight, initial_font_italic)
        self.initial_font.setBold(initial_font_bold)
        self.initial_font.setStrikeOut(initial_font_strikeout)
        self.initial_font.setUnderline(initial_font_underline)
        logger.info(f"Font: {initial_font_name}, Font style: {initial_font_style}, Weight: {initial_font_weight},"
                    f" Italic: {initial_font_italic}, Bold: {initial_font_bold}, Strikeout: {initial_font_strikeout},"
                    f" Underline: {initial_font_underline}")

    def set_always_on_top(self):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.checkbox_always_on_top.isChecked())
        on_top_config = {"ocr_window": {'always_on_top': self.checkbox_always_on_top.isChecked()}}
        update_config(on_top_config)
        self.show()

    def change_font(self):
        self.config = load_config()
        self.load_font_config()

        font_dialog = QFontDialog(self.initial_font)
        font_dialog.setWindowIcon(QIcon(app_icon))

        if font_dialog.exec() != QDialog.Accepted:
            return

        selected_font = font_dialog.selectedFont()
        self.text_edit_extracted.setFont(selected_font)
        if self.text_edit_translated is not None:
            self.text_edit_translated.setFont(selected_font)

        font_name = selected_font.family()
        font_size = selected_font.pointSize()
        font_weight = selected_font.weight()
        font_strikeout = selected_font.strikeOut()
        font_underline = selected_font.underline()
        font_style_bold = "Bold" if selected_font.bold() else "Regular"
        font_style_italic = "Italic" if selected_font.italic() else ""
        font_style_strip = f"{font_style_bold} {font_style_italic}".strip()

        font_config = {
            "ocr_window": {
                'font_name': font_name,
                'font_size': font_size,
                'font_weight': int(font_weight),
                'font_style': font_style_strip,
                'font_strikeout': font_strikeout,
                'font_underline': font_underline
            }
        }
        update_config(font_config)

        logger.info(f"Font: {font_name}, Font Style: {font_style_strip}, Size: {font_size},"
                    f" Weight: {font_weight}, Strikeout: {font_strikeout}, Underline: {font_underline}")

    def ok_button_clicked(self):
        self.save_popup_window_position()
        self.close()

    def closeEvent(self, even):
        logger.info("OCR Text window closed")


class ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()
