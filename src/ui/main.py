# Standard library
from pathlib import Path

# Third-party libraries
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QIcon, QAction, QGuiApplication
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QApplication, QSystemTrayIcon, QMenu, QStyle
from loguru import logger

# Source
from src.ui.asset_manager import app_icon
from src.ui.overlay_capture import TransparentOverlayCapture
from src.ui.settings import SettingsUI
from src.config.config import load_config, update_config


class MainUI(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyTextractOCR")
        self.setFixedSize(300, 50)
        self.setWindowIcon(QIcon(app_icon))
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.pos_y = None
        self.pos_x = None
        self.config = None
        self.saved_position = None

        # Create Settings UI once
        self.settings_ui = SettingsUI()
        self.settings_ui.finished.connect(self.on_settings_ui_closed)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.activated.connect(self.tray_icon_activated)

        icon_path = Path('assets/icon/app-icon.svg')
        if icon_path.is_file():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            # Use a built-in system icon if the custom one is missing.
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        self.tray_icon.setToolTip('System Tray Example')

        self.main_menu_action = QAction('Show PyTexractOCR')
        self.settings_action = QAction('Settings')
        self.about_action = QAction('About')
        self.exit_action = QAction('Exit')

        self.main_menu_action.setIcon(QIcon('assets/icon/screenshot.svg'))
        self.settings_action.setIcon(QIcon('assets/icon/setting-icon.svg'))
        self.about_action.setIcon(QIcon('assets/icon/info-circle-icon.svg'))
        self.exit_action.setIcon(QIcon('assets/icon/red-x-line-icon.svg'))

        self.main_menu_action.triggered.connect(self.show)
        self.settings_action.triggered.connect(self.show_settings_from_tray)
        self.about_action.triggered.connect(self.show_about_from_tray)
        self.exit_action.triggered.connect(self.exit_app_from_tray)

        self.menu = QMenu()
        self.menu.addAction(self.main_menu_action)
        self.menu.addAction(self.settings_action)
        self.menu.addAction(self.about_action)
        self.menu.addAction(self.exit_action)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()

        self.load_main_window_position()

        horizontal_layout = QHBoxLayout()

        self.capture_button = QPushButton("Capture", self)
        self.capture_button.setToolTip("Capture Rectangular Region")
        self.capture_button.setEnabled(True)
        self.capture_button.setAutoDefault(False)
        horizontal_layout.addWidget(self.capture_button)
        self.capture_button.clicked.connect(self.start_transparent_overlay)

        self.setting_button = QPushButton("Settings", self)
        self.setting_button.setEnabled(True)
        self.setting_button.setAutoDefault(False)
        horizontal_layout.addWidget(self.setting_button)
        self.setting_button.clicked.connect(self.show_settings_ui_main)

        self.setLayout(horizontal_layout)

        self.overlay_capture = TransparentOverlayCapture(self)  # Create an instance of TransparentOverlay

    def show_settings_ui_main(self):
        if not self.settings_ui.isVisible():
            self.settings_ui.initialize_settings_components()
            self.settings_ui.show()
        else:
            self.settings_ui.showNormal()
            self.settings_ui.raise_()

    # Automatically save the current position of dialog before running the screenshot
    # For function show_main_ui
    def start_transparent_overlay(self):
        self.saved_position = self.pos()
        logger.info(f"Main window saved position before screenshot: X: {self.saved_position.x()} Y: {self.saved_position.y()}")
        self.hide()
        self.overlay_capture.show_overlay()  # Show the TransparentOverlay

    # Show the MainUI dialog of the current save position
    def show_main_ui(self):
        if self.saved_position is not None:
            self.move(self.saved_position)
        self.show()
        if not self.overlay_capture.isHidden():
            self.overlay_capture.close_overlay()

    def mousePressEvent(self, event):
        logger.info("Mouse clicked")

    # Ignore the closing the MainUI dialog if OCR Text dialog is currently open
    def closeEvent(self, event):
        if self.settings_ui.isVisible():
            self.settings_ui.showNormal()
            self.settings_ui.raise_()
            event.ignore()
            return

        if self.overlay_capture.ocr_text_ui.isVisible():
            event.ignore()
            return

        self.config = load_config()
        system_tray = self.config['preferences']['minimize_to_system_tray']
        tray_notif = self.config['miscellaneous']['tray_notification_shown']
        if system_tray:
            logger.info("Minimizing application to system tray")
            if not tray_notif:
                self.tray_icon.showMessage('Hey there!', 'PyTextractOCR has been minimized to the system tray. ',
                                           QSystemTrayIcon.Information, 2000)
                update_config({"miscellaneous": {'tray_notification_shown': True}})
        else:
            self.save_main_window_position()
            event.accept()
            logger.info("Application closed")
            QCoreApplication.quit()

    # Save the current position of window dialog to configuration file before quitting
    def save_main_window_position(self):
        window_position_x = self.pos().x()
        window_position_y = self.pos().y()
        self_pos_xy = {
            "miscellaneous": {
                'main_window_position_x': window_position_x,
                'main_window_position_y': window_position_y
            }
        }
        logger.info(f"Main window saved position: X: {window_position_x} Y: {window_position_y}")
        update_config(self_pos_xy)

    # Load the save position from configuration file then move the window before showing the dialog
    # This function will only run once before starting
    def load_main_window_position(self):
        config_path = Path('config.toml')
        if config_path.is_file():
            self.config = load_config()
            pos_x = self.config['miscellaneous']['main_window_position_x']
            pos_y = self.config['miscellaneous']['main_window_position_y']
            self.move(pos_x, pos_y)
            logger.info(f"Loading main window position: X: {pos_x} Y: {pos_y}")
        else:
            # Center the dialog on the screen
            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
            logger.info(f"Moving main window position to center: X: {x}, Y: {y}")

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show()

    def show_settings_from_tray(self):
        if not self.settings_ui.isVisible():
            # self.main_menu_action.setEnabled(False)
            self.settings_ui.initialize_settings_components()
            self.settings_ui.show()

    def show_about_from_tray(self):
        pass

    def exit_app_from_tray(self):
        self.save_main_window_position()
        logger.info("Application closed using system tray")
        QCoreApplication.quit()

    def on_settings_ui_closed(self):
        logger.info("Settings window close")
        # self.main_menu_action.setEnabled(True)
