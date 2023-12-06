# Standard libraries
import tempfile
from datetime import datetime
from pathlib import Path

# Third-party libraries
from loguru import logger
from PIL import ImageGrab
from playsound import playsound, PlaysoundException  # Use version 1.2.2
from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QPainter, QColor, QPixmap, QCursor, QPen
from PySide6.QtWidgets import QMainWindow, QApplication, QLabel, QVBoxLayout, QWidget

# Sources
from src.config.config import load_config
from src.ocr.ocr_processor import perform_ocr
from src.ui.ocr_text import OCRTextUI
from src.utils.message_box import show_message_box


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.previous_pos = None
        self.start_pos = None
        self.end_pos = None
        self.selection_area = None
        self.capture_mode = False
        self.start_capture_mode = False

        self.label_dimensions = QLabel(self)
        self.label_dimensions.setStyleSheet("QLabel { color : white; background-color: rgba(0, 100, 0, 255); }")
        self.label_dimensions.setAlignment(Qt.AlignCenter)
        self.label_dimensions.setGeometry(0, 0, 140, 20)
        self.label_dimensions.hide()

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_mouse_movement)

    def mousePressEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if not self.capture_mode:
                self.start_pos = QCursor.pos()
                self.selection_area = QRect(self.start_pos, self.start_pos)
                self.label_dimensions.hide()
                self.start_capture_mode = False
                self.timer.start(10)
                self.update()
            else:
                self.start_capture_mode = True
            self.capture_mode = not self.capture_mode

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.selection_area:
            painter = QPainter(self)
            border_color = QColor('green')
            border_width = 1
            painter.setPen(QPen(border_color, border_width, Qt.SolidLine))
            painter.drawRect(self.selection_area)

    def check_mouse_movement(self):
        self.end_pos = QCursor.pos()

        if self.end_pos != self.previous_pos:
            self.selection_area = QRect(self.start_pos, self.end_pos)
            self.previous_pos = self.end_pos

            width = abs(self.start_pos.x() - self.end_pos.x())
            height = abs(self.start_pos.y() - self.end_pos.y())
            self.label_dimensions.setText(f"Width: {width}, Height: {height}")
            self.update_label_position()

            self.update()

    def update_label_position(self):
        label_width = self.label_dimensions.width()
        label_height = self.label_dimensions.height()
        label_x = self.selection_area.center().x() - label_width / 2
        label_y = self.selection_area.bottom() + 5  # Distance from the bottom
        self.label_dimensions.setGeometry(label_x, label_y, label_width, label_height)
        self.label_dimensions.show()


class GetScreenshot(QMainWindow):
    def __init__(self, main_ui_instance):
        super().__init__()

        self.config = None
        self.image_label = None
        self.image_layout = None
        self.central_widget = None
        self.extracted_text = None
        self.selection_area = None
        self.start_pos = None
        self.end_pos = None

        self.ocr_text_ui = OCRTextUI()
        self.main_ui_instance = main_ui_instance

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.image_layout = QVBoxLayout(self.central_widget)
        self.image_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = ImageLabel(self.central_widget)
        self.image_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        self.image_label.setContentsMargins(0, 0, 0, 0)
        self.image_label.setStyleSheet("QLabel { border: none; }")

    def close_fullscreen_show_main(self):
        self.close()
        self.main_ui_instance.show_main_ui()

    def capture_screenshot(self):
        self.image_label.label_dimensions.hide()

        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)

        pixmap = QPixmap(screenshot)

        # Display pixmap without margins or borders
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.showFullScreen()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.image_label.start_capture_mode:
                self.image_label.timer.stop()
                self.take_screenshot()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.image_label.timer.stop()
            self.image_label.capture_mode = False
            self.image_label.selection_area = None
            self.image_label.start_pos = None
            self.image_label.end_pos = None
            self.close_fullscreen_show_main()

    def take_screenshot(self):
        if (not self.image_label.end_pos
                or self.image_label.start_pos.x() == self.image_label.end_pos.x()
                or self.image_label.start_pos.y() == self.image_label.end_pos.y()):
            self.image_label.start_pos = None
            self.image_label.end_pos = None
            return

        try:
            self.close()
            x, y, width, height = self.calculate_selected_area()
            self.capture_selected_area(x, y, width, height)
            self.image_label.selection_area = None
            self.image_label.start_pos = None
            self.image_label.end_pos = None

        except ValueError as e:
            show_message_box("Critical", "Error", str(e))

    def calculate_selected_area(self):
        x = min(self.image_label.start_pos.x(), self.image_label.end_pos.x())
        y = min(self.image_label.start_pos.y(), self.image_label.end_pos.y())
        width = abs(self.image_label.start_pos.x() - self.image_label.end_pos.x())
        height = abs(self.image_label.start_pos.y() - self.image_label.end_pos.y())
        return x, y, width, height

    def capture_selected_area(self, x, y, width, height):
        logger.info(f"Selected area: x: {x}, y: {y}, width: {width}, height: {height}")

        self.config = load_config()
        current_datetime = get_current_datetime()

        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))  # Get a screenshot of the selected area
        output_folder = self.get_output_folder_path()

        if self.config['output']['save_captured_image']:
            captured_file_name = current_datetime + ".png"
            try:
                screenshot.save(output_folder / captured_file_name)
                logger.info(f"Screenshot saved: {output_folder}\\{captured_file_name}")

            except Exception as e:
                self.close_fullscreen_show_main()
                logger.error(f"An error occurred while taking a screenshot {e}")
                raise ValueError(f"Failed to create a screenshot file in '{output_folder}'")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
            enhanced_file_name = temp.name
            screenshot.save(enhanced_file_name)
            logger.info(f"Screenshot saved as temporary file: {enhanced_file_name}")

        if self.config['preferences']['enable_sound']:
            play_sound_file(self.config['preferences']['sound_file'])

        self.extracted_text = perform_ocr(enhanced_file_name, current_datetime)
        self.close_fullscreen_show_main()

        if self.extracted_text[0]:
            logger.success("OCR completed")

            if self.config['output']['show_popup_window']:
                self.show_ocr_text_ui()

    def get_output_folder_path(self):
        output_folder = Path(self.config['output']['output_folder_path'])

        if not output_folder.exists() and not output_folder.is_dir():
            try:
                output_folder.mkdir(parents=True, exist_ok=True)
                logger.success(f"Output folder created successfully '{output_folder}'")

            except Exception as e:
                self.close_fullscreen_show_main()
                logger.error(f"Failed to create output folder: {e}")
                raise ValueError("Failed to create output folder.")

        return output_folder

    def show_ocr_text_ui(self):
        self.ocr_text_ui.init_ui()
        if not self.ocr_text_ui.isVisible():
            self.ocr_text_ui.show()
        else:
            self.ocr_text_ui.raise_()
        self.ocr_text_ui.set_extracted_text(self.extracted_text[0])
        if self.extracted_text[1] is not None:
            self.ocr_text_ui.set_translated_text(self.extracted_text[1])


def play_sound_file(sound_file):
    if Path(sound_file).exists():
        try:
            playsound(sound_file.replace('\\', '/'), False)
            logger.success(f"Sound file has been played successfully using playsound")

        except PlaysoundException as e:
            logger.error(f"An error occurred while playing the sound file '{sound_file}' {e} ")
    else:
        logger.error(f"{sound_file} doesnt exist")


def get_current_datetime():
    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour  # 24-hour format (military hour)
    minute = now.minute
    second = now.second
    current_datetime = f"{year}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}"
    logger.info(f"Current date and time: {current_datetime}")
    return current_datetime
