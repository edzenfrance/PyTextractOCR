# Standard libraries
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

# Third-party libraries
from loguru import logger
from PIL import ImageGrab
from playsound import playsound, PlaysoundException  # Use version 1.2.2
from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QPainter, QColor, QPixmap, QCursor, QPen, QGuiApplication
from PySide6.QtWidgets import QMainWindow, QApplication, QLabel, QVBoxLayout, QWidget

# Custom libraries
from src.config.config import load_config
from src.ocr.ocr_processor import perform_ocr
from src.ui.ocr_text import OCRTextUI
from src.utils.message_box import show_message_box
from src.utils.translate import translate_text


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
        self.label_dimensions.setStyleSheet("QLabel { color : black; background-color: rgba(248, 248, 186, 255); "
                                            "border-bottom: 2px solid gray; border-right: 2px solid gray; }")
        self.label_dimensions.setAlignment(Qt.AlignCenter)
        self.label_dimensions.setGeometry(0, 0, 65, 20)
        self.label_dimensions.hide()

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_mouse_movement)

    def mousePressEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.handle_left_button_event()

        if event.buttons() & Qt.RightButton:
            self.handle_right_button_event()

    def handle_left_button_event(self):
        if not self.capture_mode:
            self.initiate_capture_mode()
        else:
            self.update_capture_mode()

    def handle_right_button_event(self):
        self.capture_mode = False
        self.selection_area = QRect()
        self.label_dimensions.hide()
        self.timer.stop()
        self.update()

    def initiate_capture_mode(self):
        self.start_pos = QCursor.pos()
        self.selection_area = QRect(self.start_pos, self.start_pos)
        self.label_dimensions.hide()
        self.start_capture_mode = False
        self.capture_mode = True
        self.timer.start(10)
        self.update()

    def update_capture_mode(self):
        if not (self.start_pos.x() == self.end_pos.x() and self.start_pos.y() == self.end_pos.y()):
            self.start_capture_mode = True
            self.capture_mode = False

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.selection_area:
            painter = QPainter(self)
            border_color = QColor(117, 255, 255, 255)
            border_width = 1
            painter.setPen(QPen(border_color, border_width, Qt.SolidLine))
            painter.drawRect(self.selection_area)

    def check_mouse_movement(self):
        self.end_pos = QCursor.pos()
        if self.end_pos != self.previous_pos:
            self.selection_area = QRect(self.start_pos, self.end_pos)
            self.previous_pos = self.end_pos

            width = abs(self.start_pos.x() - self.end_pos.x()) + 1
            height = abs(self.start_pos.y() - self.end_pos.y()) + 1
            self.label_dimensions.setText(f"{width} x {height}")
            self.update_label_position()
            self.update()

    def update_label_position(self):
        label_width = self.label_dimensions.sizeHint().width() + 8  # Auto-adjust label width based on text length
        label_height = self.label_dimensions.height()
        screen_resolution = QGuiApplication.primaryScreen().geometry()
        screen_width, screen_height = screen_resolution.width(), screen_resolution.height()
        # Determine the direction of mouse movement
        moving_right = self.end_pos.x() > self.start_pos.x()
        moving_down = self.end_pos.y() > self.start_pos.y()
        # Adjust label position based on mouse movement direction
        # Adjust the offsets (10 and 5) to control the spacing around the label, increase these values to add more space
        label_x = self.end_pos.x() + 10 if moving_right else self.end_pos.x() - label_width - 5
        label_y = self.end_pos.y() + 10 if moving_down else self.end_pos.y() - label_height - 5
        # Check if label would exceed screen width
        if label_x + label_width > screen_width:
            label_x = screen_width - label_width
        elif label_x < 0:
            label_x = 0
        # Check if label would exceed screen height
        if label_y + label_height > screen_height:
            label_y = screen_height - label_height
        elif label_y < 0:
            label_y = 0
        self.label_dimensions.setGeometry(label_x, label_y, label_width, label_height)
        self.label_dimensions.show()


class FullscreenCapture(QMainWindow):
    def __init__(self, main_ui_instance):
        super().__init__()

        self.config = None
        self.image_label = None
        self.image_layout = None
        self.central_widget = None
        self.crosshair_cursor = None
        self.extracted_text = None
        self.translated_text = None
        self.selection_area = None
        self.start_pos = None
        self.end_pos = None

        # OCR Text instance
        self.ocr_text_ui = OCRTextUI()

        # Dependency Injection for MainUI show_main_ui method, injects an instance of MainUI class into this class
        self.main_ui_instance = main_ui_instance

        self.init_image_label()
        self.init_crosshair_cursor()

    def init_image_label(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.image_layout = QVBoxLayout(self.central_widget)
        self.image_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = ImageLabel(self.central_widget)
        self.image_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

    def init_crosshair_cursor(self):
        crosshair_size = 25

        pixmap_size = crosshair_size * 4
        pixmap = QPixmap(pixmap_size, pixmap_size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        pen = painter.pen()
        pen.setWidth(1)  # Thickness of the crosshair
        pen.setColor(QColor(177, 255, 255, 255))
        painter.setPen(pen)

        # Center point of the pixmap
        center_x = pixmap_size // 2
        center_y = pixmap_size // 2

        # Half-size of the crosshair lines
        half_size = (crosshair_size - 1) // 2

        # Draw the crosshair on the pixmap
        painter.drawLine(center_x - half_size, center_y, center_x + half_size, center_y)  # Horizontal line
        painter.drawLine(center_x, center_y - half_size, center_x, center_y + half_size)  # Vertical line
        painter.end()

        self.crosshair_cursor = QCursor(pixmap, center_x - 2, center_y - 2)

    def close_fullscreen_show_main(self):
        self.close()
        self.main_ui_instance.show_main_ui()

    def get_fullscreen_capture(self):
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        pixmap = QPixmap(screenshot)

        # Display pixmap without margins or borders
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())

        self.image_label.label_dimensions.hide()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.showFullScreen()
        self.setCursor(self.crosshair_cursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.image_label.start_capture_mode:
                self.image_label.timer.stop()
                self.process_selected_area()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.image_label.timer.stop()
            self.image_label.capture_mode = False
            self.image_label.selection_area = None
            self.image_label.start_pos = None
            self.image_label.end_pos = None
            self.close_fullscreen_show_main()

    def process_selected_area(self):
        if (self.image_label.start_pos.x() == self.image_label.end_pos.x() and self.image_label.start_pos.y() == self.image_label.end_pos.y()
                or not self.image_label.end_pos):
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
        width = abs(self.image_label.start_pos.x() - self.image_label.end_pos.x()) + 1
        height = abs(self.image_label.start_pos.y() - self.image_label.end_pos.y()) + 1
        logger.info(f"Selected area: x: {x}, y: {y}, width: {width}, height: {height}")
        return x, y, width, height

    def capture_selected_area(self, x, y, width, height):
        self.config = load_config()
        current_datetime = self.get_current_datetime()
        output_folder = self.get_output_folder_path()

        # Get a capture of the selected area
        capture_area = ImageGrab.grab(bbox=(x, y, x + width, y + height))

        if self.config['output']['save_captured_image']:
            try:
                capture_file_name = current_datetime + ".png"
                capture_area.save(output_folder / capture_file_name)
                logger.success(f"Captured image saved: {output_folder}\\{capture_file_name}")
            except Exception as e:
                self.close_fullscreen_show_main()
                logger.error(f"An error occurred while capturing {e}")
                raise ValueError(f"Failed to create a capture file in '{output_folder}'")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
            temporary_file_name = temp.name
            capture_area.save(temporary_file_name)
            logger.success(f"Captured image saved as temporary file: {temporary_file_name}")

        self.start_perform_ocr(temporary_file_name, current_datetime, False)

    def start_perform_ocr(self, file_name, current_datetime, scan_only):
        self.config = load_config()
        if scan_only:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
                temporary_file_name = temp.name
                shutil.copy(file_name, temporary_file_name)  # copy the selected file to the temporary file
                logger.success(f"Selected image copied as temporary file: {temp.name}")
            self.extracted_text = perform_ocr(temporary_file_name, self.config)
            self.translated_text = self.translate_extracted_text(self.extracted_text)
        else:
            self.extracted_text = perform_ocr(file_name, self.config)
            self.translated_text = self.translate_extracted_text(self.extracted_text)
            self.save_or_remove_temporary_image(file_name, current_datetime)
        self.play_sound_file()
        self.close_fullscreen_show_main()
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
        if not self.extracted_text or not self.config['output']['show_popup_window']:
            return

        self.ocr_text_ui.init_ui()
        self.ocr_text_ui.show() if not self.ocr_text_ui.isVisible() else self.ocr_text_ui.raise_()
        self.ocr_text_ui.set_extracted_text(self.extracted_text)
        self.ocr_text_ui.set_translated_text(self.translated_text)

    def play_sound_file(self):
        if not self.extracted_text or not self.config['preferences']['enable_sound']:
            return

        sound_file = self.config['preferences']['sound_file']
        if not Path(sound_file).exists():
            logger.error(f"{sound_file} does not exist")
            return

        try:
            playsound(sound_file.replace('\\', '/'), False)
            logger.success(f"Sound file has been played successfully using playsound")
        except PlaysoundException as e:
            logger.error(f"An error occurred while playing the sound file '{sound_file}' {e} ")

    @staticmethod
    def get_current_datetime():
        now = datetime.now()
        # The hour is in a 24-hour format (military time)
        return f"{now.year}_{now.month:02d}_{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}"

    def translate_extracted_text(self, extracted_text):
        if self.config['translate']['enable_translation']:
            try:
                logger.info(f"Translating text using google translate")
                translated_text = translate_text(extracted_text, self.config)
                logger.info(f"Translated Text ({translated_text[1]}):\n{translated_text[0]}")
            except Exception as e:
                translated_text = None
                logger.error(f"An error occurred while translating text: {e}")
            return translated_text

    def save_or_remove_temporary_image(self, file_name, current_datetime):
        if self.config['output']['save_enhanced_image']:
            folder = self.config['output']['output_folder_path']
            self.save_temporary_image(file_name, current_datetime, folder)
        else:
            self.remove_temporary_image(file_name)

    @staticmethod
    def save_temporary_image(image_path, date_time, output_folder_path):
        new_image_path = os.path.join(output_folder_path, f"{date_time}_enhanced.png")
        try:
            shutil.move(image_path, new_image_path)
            logger.info(f"The file '{image_path}' has been moved to '{new_image_path}'")
        except Exception as e:
            logger.error(f"Failed to move the file '{image_path}' to '{new_image_path}: {e}")

    @staticmethod
    def remove_temporary_image(image_path):
        try:
            os.remove(image_path)
            logger.success(f"Temporary image successfully removed: {image_path}")
        except Exception as e:
            logger.error(f"An error occurred while removing temporary image '{image_path}': {e}")
