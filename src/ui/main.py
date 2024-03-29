# Standard libraries
import time
from pathlib import Path

# Third-party libraries
from loguru import logger
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QIcon, QAction, QGuiApplication
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QSystemTrayIcon, QMenu, QStyle, QFileDialog

# Custom libraries
from src.config.config import load_config, update_config
from src.ui.asset_manager import app_icon, main_icon, settings_icon, about_icon, exit_icon
from src.ui.capture import FullscreenCapture
from src.ui.settings import SettingsUI
from src.ui.about import AboutUI


class MainUI(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyTextractOCR")
        self.setFixedSize(300, 50)
        self.setWindowIcon(QIcon(app_icon))
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.load_main_window_position()

        self.pos_y = None
        self.pos_x = None
        self.saved_position = None
        self.ocr_text_ui_visible = False
        self.settings_ui_visible = False
        self.open_file_dialog_path = None

        # Settings UI instance
        self.settings_ui = SettingsUI()
        self.settings_ui.finished.connect(self.on_settings_ui_closed)

        # About UI instance
        self.about_ui = AboutUI()

        # Fullscreen Capture instance
        self.fullscreen_capture = FullscreenCapture(self)

        # System Tray Icon instance
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.activated.connect(self.tray_icon_activated)

        icon_path = Path(app_icon)
        # SP_MessageBoxInformation - Built-in system icon if the custom icon is missing
        self.tray_icon.setIcon(QIcon(str(icon_path)) if icon_path.is_file else self.style().standardIcon(QStyle.SP_MessageBoxInformation))

        self.main_menu_action = QAction('Show PyTexractOCR', triggered=self.show)
        self.settings_action = QAction('Settings', triggered=self.show_settings_from_tray)
        self.about_action = QAction('About', triggered=self.show_about_from_tray)
        self.exit_action = QAction('Exit', triggered=self.exit_app_from_tray)

        self.main_menu_action.setIcon(QIcon(main_icon))
        self.settings_action.setIcon(QIcon(settings_icon))
        self.about_action.setIcon(QIcon(about_icon))
        self.exit_action.setIcon(QIcon(exit_icon))

        self.menu = QMenu()
        self.menu.addAction(self.main_menu_action)
        self.menu.addAction(self.settings_action)
        self.menu.addAction(self.about_action)
        self.menu.addAction(self.exit_action)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()
        self.tray_icon.setToolTip("PyTextractOCR")

        horizontal_layout = QHBoxLayout()

        capture_button = QPushButton("Capture", self)
        capture_button.setToolTip("Capture Rectangular Region")
        capture_button.setAutoDefault(False)
        capture_button.clicked.connect(self.start_fullscreen_capture)

        scan_button = QPushButton("Scan", self)
        scan_button.setToolTip("Select and OCR Image")
        scan_button.setAutoDefault(False)
        scan_button.clicked.connect(self.select_image_to_ocr)

        settings_button = QPushButton("Settings", self)
        settings_button.setToolTip("Open Settings window")
        settings_button.setAutoDefault(False)
        settings_button.clicked.connect(self.show_settings_ui_main)

        horizontal_layout.addWidget(capture_button)
        horizontal_layout.addWidget(scan_button)
        horizontal_layout.addWidget(settings_button)

        self.setLayout(horizontal_layout)

    def show_settings_ui_main(self):
        if not self.settings_ui.isVisible():
            self.settings_ui.initialize_settings_components()
            self.settings_ui.show()
        else:
            self.settings_ui.showNormal()
            self.settings_ui.raise_()

    def start_fullscreen_capture(self):
        self.saved_position = self.pos()  # Save the current position of window before capturing. Use for show_main_ui function
        logger.info(f"Main window saved position before capture: X: {self.saved_position.x()} Y: {self.saved_position.y()}")
        self.hide()  # Hide the MainUI window
        self.hide_other_ui_before_capture()
        time.sleep(0.3)  # Add a sleep to wait for the MainUI window to be fully hidden before capturing
        self.fullscreen_capture.get_fullscreen_capture()  # Start capturing of fullscreen

    def select_image_to_ocr(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image File", self.open_file_dialog_path,
                                                   "Image Files (*.jpg *.png *.bmp *.gif *.jpeg *.tiff *.webp)", options=options)
        if file_path:
            formatted_file_path = file_path.replace('/', '\\')
            self.open_file_dialog_path = formatted_file_path
            datetime = self.fullscreen_capture.get_current_datetime()
            self.fullscreen_capture.ocr_text_ui.save_popup_window_position()
            logger.info(f"Selected image for OCR: {formatted_file_path}")
            self.fullscreen_capture.start_perform_ocr(formatted_file_path, datetime, True)

    def hide_other_ui_before_capture(self):
        if self.fullscreen_capture.ocr_text_ui.isVisible():
            self.fullscreen_capture.ocr_text_ui.save_popup_window_position()
            self.ocr_text_ui_visible = True
            self.fullscreen_capture.ocr_text_ui.hide()

        if self.settings_ui.isVisible():
            self.settings_ui.save_settings_window_position()
            self.settings_ui_visible = True
            self.settings_ui.hide()

    def show_other_ui_after_capture(self):
        if self.ocr_text_ui_visible:
            self.ocr_text_ui_visible = False
            self.fullscreen_capture.ocr_text_ui.show()

        if self.settings_ui_visible:
            self.settings_ui.load_settings_window_position()
            self.settings_ui_visible = False
            self.settings_ui.show()

    # Show the MainUI window at the saved position
    def show_main_ui(self):
        if self.saved_position is not None:
            self.move(self.saved_position)
        self.show()
        self.show_other_ui_after_capture()

        if not self.fullscreen_capture.isHidden():
            self.fullscreen_capture.close_fullscreen_show_main()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            event.ignore()

    def closeEvent(self, event):
        # Ignore the closing the MainUI window if Settings window is currently open
        if self.settings_ui.isVisible():
            self.settings_ui.showNormal()
            self.settings_ui.raise_()
            event.ignore()
            return

        # Ignore the closing the MainUI window if OCR Text window is currently open
        if self.fullscreen_capture.ocr_text_ui.isVisible():
            self.fullscreen_capture.ocr_text_ui.showNormal()
            self.fullscreen_capture.ocr_text_ui.raise_()
            event.ignore()
            return

        config = load_config()
        if config['preferences']['minimize_to_system_tray']:
            logger.info("Minimizing application to system tray")

            if not config['miscellaneous']['tray_notification_shown']:
                self.tray_icon.showMessage('Hey there!', 'PyTextractOCR has been minimized to the system tray. ',
                                           QSystemTrayIcon.Information, 2000)
                update_config({"miscellaneous": {'tray_notification_shown': True}})
        else:
            self.save_main_window_position()
            event.accept()
            logger.info("Application closed")
            QCoreApplication.quit()

    # Save the current position of window before quitting
    def save_main_window_position(self):
        window_position_x = self.pos().x()
        window_position_y = self.pos().y()
        self_pos_xy = {"miscellaneous": {'main_window_position_x': window_position_x, 'main_window_position_y': window_position_y}}
        logger.info(f"Main window saved position: X: {window_position_x} Y: {window_position_y}")
        update_config(self_pos_xy)

    def load_main_window_position(self):
        config_path = Path('config.toml')
        if config_path.is_file():
            # Move the window at the saved position
            config = load_config()
            pos_x = config['miscellaneous']['main_window_position_x']
            pos_y = config['miscellaneous']['main_window_position_y']
            logger.info(f"Moving main window position: X: {pos_x} Y: {pos_y}")
            self.move(pos_x, pos_y)
        else:
            # Center the window on the screen if the configuration file is not found
            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            logger.info(f"Moving main window position to center: X: {x}, Y: {y}")
            self.move(x, y)

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show()

    def show_settings_from_tray(self):
        if not self.settings_ui.isVisible():
            logger.info("Showing settings using system tray")
            self.settings_action.setEnabled(False)
            self.settings_ui.initialize_settings_components()
            self.settings_ui.show()

    def show_about_from_tray(self):
        self.about_ui.show()

    def exit_app_from_tray(self):
        self.save_main_window_position()
        logger.info("Application closed using system tray")
        QCoreApplication.quit()

    def on_settings_ui_closed(self):
        self.settings_action.setEnabled(True)
        logger.info("Emit - Settings window closed")
        # self.main_menu_action.setEnabled(True)
