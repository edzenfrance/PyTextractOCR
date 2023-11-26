# Standard libraries
import tempfile
from datetime import datetime
from pathlib import Path

# Third-party libraries
from loguru import logger
from PIL import ImageGrab
from playsound import playsound, PlaysoundException  # Use version 1.2.2
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QMainWindow

# Sources
from src.config.config import load_config
from src.ocr.ocr_processor import perform_ocr
from src.ui.ocr_text import OCRTextUI
from src.utils.message_box import show_message_box


class TransparentOverlayCapture(QMainWindow):
    def __init__(self, main_ui_instance):
        super().__init__()

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setWindowOpacity(0.1)  # Set the window's opacity to 10% (very transparent)

        self.returned_text = None
        self.show_formatted_text = None
        self.filename = None
        self.drag_area = None
        self.drag_start_pos = None
        self.drag_end_pos = None

        self.ocr_text_ui = OCRTextUI()
        self.main_ui_instance = main_ui_instance

    def show_overlay(self):
        self.show()  # Show the overlay window

    def close_overlay(self):
        self.drag_area = None
        self.close()  # Hide the overlay window

    def close_overlay_then_show_main(self):
        self.close_overlay()
        self.main_ui_instance.show_main_ui()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))  # Make the overlay transparent
        if self.drag_area:
            painter.setOpacity(0.0)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.setBrush(QColor('white'))
            painter.drawRect(self.drag_area)

    def mousePressEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint()
            self.drag_area = QRect(self.drag_start_pos, self.drag_start_pos)
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.drag_end_pos = event.globalPosition().toPoint()
            self.drag_area = QRect(self.drag_start_pos, self.drag_end_pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.take_screenshot()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_overlay_then_show_main()

    def take_screenshot(self):
        if self.drag_area:
            try:
                # Get the coordinates of the selected area
                if self.drag_start_pos is not None and self.drag_end_pos is not None:
                    x = min(self.drag_start_pos.x(), self.drag_end_pos.x())
                    y = min(self.drag_start_pos.y(), self.drag_end_pos.y())
                    width = abs(self.drag_start_pos.x() - self.drag_end_pos.x())
                    height = abs(self.drag_start_pos.y() - self.drag_end_pos.y())

                    self.capture_selected_area(x, y, width, height)
                    self.drag_start_pos = None
                    self.drag_end_pos = None

            except ValueError as e:
                show_message_box("Critical", "Error", str(e))

    def capture_selected_area(self, x, y, width, height):
        logger.info(f"x: {x}, y: {y}, width: {width}, height: {height}")

        config = load_config()
        current_datetime = get_current_datetime()
        directory = Path(config['output']['output_folder_path'])
        added_name = "pytexractocr_"

        # Capture the screenshot of the selected area
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))

        if config['output']['auto_save_capture']:
            self.filename = added_name + current_datetime + ".png"

            if not directory.exists() and not directory.is_dir():
                try:
                    directory.mkdir()
                    logger.success(f"Folder created successfully {directory}")

                except Exception as e:
                    self.close_overlay_then_show_main()
                    logger.error(f"An error occurred while creating folder {e}")
                    raise ValueError(f"Failed to create output folder.\n\nThe system cannot find the path specified: '{directory}'")
            try:
                screenshot.save(directory / self.filename)
                logger.info(f"Screenshot saved: {directory}\\{added_name}{current_datetime}.png")

            except Exception as e:
                self.close_overlay_then_show_main()
                logger.error(f"An error occurred while taking a screenshot {e}")
                raise ValueError(f"Failed to create a screenshot file in '{directory}'")
        else:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
                self.filename = temp.name
                screenshot.save(self.filename)
                logger.info(f"Screenshot saved as temporary file '{self.filename}'")

        if config['preferences']['enable_sound']:
            play_sound_file(config['preferences']['sound_file'])

        self.close_overlay()
        self.returned_text = perform_ocr(self.filename)
        self.main_ui_instance.show_main_ui()
        if self.returned_text[0] is not None:
            logger.success("Screenshot taken and OCR completed")
            if config['output']['show_popup_window']:
                self.show_ocr_text_ui()

    def show_ocr_text_ui(self):
        self.ocr_text_ui.init_ui()
        if not self.ocr_text_ui.isVisible():
            self.ocr_text_ui.show()
        else:
            self.ocr_text_ui.raise_()
        self.ocr_text_ui.set_extracted_text(self.returned_text[0])
        if self.returned_text[1] is not None:
            self.ocr_text_ui.set_translated_text(self.returned_text[1])


def play_sound_file(sound_file):
    if Path(sound_file).exists():
        try:
            sound_file = sound_file.replace('\\', '/')
            playsound(sound_file, False)
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
