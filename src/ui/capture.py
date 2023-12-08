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
        self.label_dimensions.setStyleSheet("QLabel { color : black; background-color: rgba(248, 248, 186, 255); "
                                            "border-bottom: 2px solid gray; border-right: 2px solid gray; }")
        self.label_dimensions.setAlignment(Qt.AlignCenter)
        self.label_dimensions.setGeometry(0, 0, 65, 20)
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
                self.capture_mode = True
                self.timer.start(10)
                self.update()
            else:
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
        label_x = self.selection_area.center().x() - label_width / 2
        label_y = self.selection_area.bottom() + 4  # Distance from the bottom
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
        self.selection_area = None
        self.start_pos = None
        self.end_pos = None

        self.ocr_text_ui = OCRTextUI()
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
        self.image_label.label_dimensions.hide()

        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)

        pixmap = QPixmap(screenshot)

        # Display pixmap without margins or borders
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())

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
            capture_file_name = current_datetime + ".png"

            try:
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

        self.extracted_text = perform_ocr(temporary_file_name, current_datetime)

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
        if self.extracted_text[0]:
            logger.success("OCR completed")
            if self.config['output']['show_popup_window']:
                self.ocr_text_ui.init_ui()
                self.ocr_text_ui.show() if not self.ocr_text_ui.isVisible() else self.ocr_text_ui.raise_()
                self.ocr_text_ui.set_extracted_text(self.extracted_text[0])
                if self.extracted_text[1]:
                    self.ocr_text_ui.set_translated_text(self.extracted_text[1])

    def play_sound_file(self):
        if not self.extracted_text[0]:
            return
        if self.config['preferences']['enable_sound']:
            sound_file = self.config['preferences']['sound_file']
            if Path(sound_file).exists():
                try:
                    playsound(sound_file.replace('\\', '/'), False)
                    logger.success(f"Sound file has been played successfully using playsound")

                except PlaysoundException as e:
                    logger.error(f"An error occurred while playing the sound file '{sound_file}' {e} ")
            else:
                logger.error(f"{sound_file} does not exist")

    @staticmethod
    def get_current_datetime():
        now = datetime.now()
        # The hour is in a 24-hour format (military time)
        return f"{now.year}_{now.month:02d}_{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}"
