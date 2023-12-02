# Standard libraries
import re
import shutil
import socket
import time
from pathlib import Path
from urllib import request, error

# Third-party libraries
import requests
from loguru import logger
from PySide6.QtCore import Qt, QRect, QTimer, QEvent, QThread, Signal
from PySide6.QtGui import QColor, QPalette, QIcon, QPainter
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog,
                               QDoubleSpinBox, QFileDialog, QHeaderView, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QProgressBar, QScrollArea,
                               QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout,
                               QWidget, QGroupBox)

# Source
from src.config.config import load_config, update_config
from src.ui.asset_manager import app_icon
from src.utils.message_box import show_message_box
from src.utils.translate import language_list, language_set


class SettingsUI(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings")
        self.setFixedSize(434, 334)
        self.setWindowIcon(QIcon(app_icon))
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowTitleHint)

        self.initialize_settings_components_finish = False
        self.ocr_tab_hide_widgets = False
        self.output_folder_created = True
        self.open_file_dialog_path = None
        self.open_folder_dialog_path = None
        self.widget_language_name = None

        # Dictionary to store QLineEdit widgets and their event handling logic
        self.line_edits = {}
        self.spinboxes = {}

        self.config = load_config()

        # Initialize timer for fading effect
        self.fade_timer = QTimer()
        self.fade_timer.setInterval(50)  # Adjust the interval for a smoother transition
        self.fade_timer.timeout.connect(self.update_apply_button_state)

        self.horizontal_layout_widget = QWidget(self)
        self.horizontal_layout_widget.setObjectName('horizontal_layout_widget')
        self.horizontal_layout_widget.setGeometry(QRect(180, 300, 244, 31))

        self.horizontal_buttons_layout = QHBoxLayout(self.horizontal_layout_widget)
        self.horizontal_buttons_layout.setObjectName('horizontal_buttons_layout')
        self.horizontal_buttons_layout.setContentsMargins(0, 0, 0, 0)

        # BUTTON - Apply
        self.button_apply_was_enabled = False
        self.button_apply_settings = QPushButton(self.horizontal_layout_widget)
        self.button_apply_settings.setObjectName('button_apply_settings')
        self.button_apply_settings.setEnabled(False)
        self.button_apply_settings.setAutoDefault(False)
        palette = QPalette()
        gray_color = QColor(128, 128, 128)
        palette.setColor(QPalette.ButtonText, gray_color)
        self.button_apply_settings.setPalette(palette)
        self.button_apply_settings.clicked.connect(self.apply_button_clicked)
        self.horizontal_buttons_layout.addWidget(self.button_apply_settings)

        # BUTTON - OK
        self.button_OK_settings = QPushButton(self.horizontal_layout_widget)
        self.button_OK_settings.setObjectName('button_OK_settings')
        self.button_OK_settings.setAutoDefault(True)
        self.button_OK_settings.clicked.connect(self.ok_button_clicked)
        self.horizontal_buttons_layout.addWidget(self.button_OK_settings)

        # BUTTON - Cancel
        self.button_cancel_settings = QPushButton(self.horizontal_layout_widget)
        self.button_cancel_settings.setObjectName('button_cancel_settings')
        self.button_cancel_settings.setAutoDefault(False)
        self.button_cancel_settings.clicked.connect(self.cancel_button)
        self.horizontal_buttons_layout.addWidget(self.button_cancel_settings)

        # TAB WIDGET
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName('tab_widget')
        self.tab_widget.setGeometry(QRect(10, 8, 415, 291))

        # ======== PREFERENCES TAB ========
        self.preferences_tab = QWidget()
        self.preferences_tab.setObjectName('preferences_tab')

        # CHECKBOX - Minimize system tray on close
        self.checkbox_minimize_to_sys_tray = QCheckBox(self.preferences_tab)
        self.checkbox_minimize_to_sys_tray.setObjectName('checkbox_minimize_to_sys_tray')
        self.checkbox_minimize_to_sys_tray.setGeometry(QRect(16, 10, 210, 20))
        self.checkbox_minimize_to_sys_tray.stateChanged.connect(self.toggle_apply_button)

        # CHECKBOX - Play sound on capture
        self.checkbox_play_sound = QCheckBox(self.preferences_tab)
        self.checkbox_play_sound.setObjectName('checkbox_play_sound')
        self.checkbox_play_sound.setGeometry(QRect(16, 40, 141, 20))
        self.checkbox_play_sound.stateChanged.connect(self.toggle_apply_button)

        # LABEL - Sound file
        self.label_sound_file = QLabel(self.preferences_tab)
        self.label_sound_file.setObjectName('label_sound_file')
        self.label_sound_file.setGeometry(QRect(15, 73, 81, 16))

        # LINE EDIT - Sound file
        self.line_edit_sound_file = QLineEdit(self.preferences_tab)
        self.line_edit_sound_file.setObjectName('line_edit_sound_file')
        self.line_edit_sound_file.setGeometry(QRect(95, 71, 251, 22))
        self.line_edit_sound_file.setCursorPosition(0)
        self.line_edit_sound_file.textChanged.connect(self.toggle_apply_button)
        self.line_edits['line_edit_sound_file'] = self.line_edit_sound_file  # Add to the dictionary

        # BUTTON - ...
        self.button_sound_file = QPushButton(self.preferences_tab)
        self.button_sound_file.setObjectName('button_sound_file')
        self.button_sound_file.setGeometry(QRect(350, 70, 24, 24))
        self.button_sound_file.setAutoDefault(False)
        self.button_sound_file.clicked.connect(self.select_audio_file)

        self.tab_widget.addTab(self.preferences_tab, '')

        # ======== OCR TAB ========
        self.ocr_tab = QWidget()
        self.ocr_tab.setObjectName('ocr_tab')

        # LABEL - OCR Language
        self.label_ocr_language = QLabel(self.ocr_tab)
        self.label_ocr_language.setObjectName('label_ocr_language')
        self.label_ocr_language.setGeometry(QRect(15, 16, 90, 16))

        # BUTTON - Show | Hide
        self.button_ocr_language = QPushButton(self.ocr_tab)
        self.button_ocr_language.setObjectName('button__show_all_lang')
        self.button_ocr_language.setGeometry(111, 12, 86, 24)
        self.button_ocr_language.setAutoDefault(False)
        self.button_ocr_language.clicked.connect(self.toggle_ocr_tab_widgets_display)

        # SCROLL AREA
        self.scroll_area = QScrollArea(self.ocr_tab)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setGeometry(QRect(5, 41, 399, 217))
        self.scroll_area.setVisible(False)

        # Widget for the scroll area
        self.scroll_content = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_content)

        # Layout for the scroll content
        self.scroll_content_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_content_layout)

        # Add checkboxes for different languages with "Download" button
        self.sc_checkbox_dict = {}
        self.sc_button_dict = {}
        self.sc_progressbar_dict = {}
        self.sc_checkboxes = []

        for language_name in language_set().values():
            self.scroll_row_layout = QHBoxLayout()
            self.sc_checkbox = QCheckBox(language_name.title())
            self.sc_button = QPushButton("Download")
            self.sc_button.setFixedSize(115, 22)
            self.sc_button.setAutoDefault(False)
            self.sc_progressbar = QProgressBar()
            self.sc_progressbar.setFixedSize(115, 22)
            self.sc_progressbar.setVisible(False)
            self.sc_progressbar.setTextVisible(False)

            self.scroll_row_layout.addWidget(self.sc_checkbox)
            self.scroll_row_layout.addWidget(self.sc_button)
            self.scroll_row_layout.addWidget(self.sc_progressbar)
            self.scroll_content_layout.addLayout(self.scroll_row_layout)

            self.sc_checkbox_dict[language_name] = self.sc_checkbox
            self.sc_button_dict[language_name] = self.sc_button
            self.sc_progressbar_dict[language_name] = self.sc_progressbar
            self.sc_checkboxes.append(self.sc_checkbox)
            self.sc_checkbox.stateChanged.connect(self.toggle_apply_button)
            self.sc_button.clicked.connect(self.download_from_github)

        if 'english' in self.sc_checkbox_dict:
            self.sc_checkbox_dict['english'].setChecked(True)

        # LABEL - Page segmentation mode
        self.label_psm_value = QLabel(self.ocr_tab)
        self.label_psm_value.setObjectName('label_psm_value')
        self.label_psm_value.setGeometry(QRect(15, 48, 119, 16))

        # COMBOBOX - Page segmentation mode
        self.combobox_psm_value = QComboBox(self.ocr_tab)
        self.combobox_psm_value.setObjectName('combobox_psm_value')
        self.combobox_psm_value.setGeometry(QRect(135, 45, 61, 22))
        self.combobox_psm_value.addItems(['3', '4', '5', '6', '7', '8', '9', '10', '11', '13'])
        psm_value = self.config['ocr']['page_segmentation_mode']
        try:
            psm_value = int(psm_value)
            if psm_value < 3 or psm_value == 12 or psm_value > 13:
                self.combobox_psm_value.setCurrentIndex(3)
            else:
                self.combobox_psm_value.setCurrentText(str(psm_value))
        except ValueError as e:
            logger.error(f"Error converting psm value to integer: {e}")
        self.toggle_checkbox_psm_tooltip(psm_value)
        self.combobox_psm_value.currentIndexChanged.connect(lambda index: (self.toggle_checkbox_psm_tooltip(index), self.toggle_apply_button()))

        # LABEL - OCR Engine mode
        self.label_oem_value = QLabel(self.ocr_tab)
        self.label_oem_value.setObjectName('label_oem_value')
        self.label_oem_value.setGeometry(QRect(222, 48, 101, 16))

        # COMBOBOX - OCR Engine mode
        self.combobox_oem_value = QComboBox(self.ocr_tab)
        self.combobox_oem_value.setObjectName('combobox_oem_value')
        self.combobox_oem_value.setGeometry(QRect(330, 45, 61, 22))
        self.combobox_oem_value.addItems(['0', '1', '2', '3'])
        oem_value = self.config['ocr']['ocr_engine_mode']
        try:
            oem_value = int(oem_value)
            if oem_value > 3:
                self.combobox_oem_value.setCurrentIndex(3)
            elif oem_value >= 0:  # -1 means the text was not found
                self.combobox_oem_value.setCurrentIndex(oem_value)
        except ValueError as e:
            logger.error(f"Error converting oem value to integer: {e}")
        self.toggle_checkbox_oem_tooltip(oem_value)
        self.combobox_oem_value.currentIndexChanged.connect(lambda index: (self.toggle_checkbox_oem_tooltip(index), self.toggle_apply_button()))

        # CHECKBOX - Preserve interword spaces
        self.checkbox_preserve_interword_spaces = QCheckBox(self.ocr_tab)
        self.checkbox_preserve_interword_spaces.setObjectName('checkbox_preserve_interword_spaces')
        self.checkbox_preserve_interword_spaces.setGeometry(QRect(16, 75, 171, 20))
        self.checkbox_preserve_interword_spaces.stateChanged.connect(self.toggle_apply_button)

        # LABEL - Blacklist characters
        self.label_blacklist_char = QLabel(self.ocr_tab)
        self.label_blacklist_char.setObjectName('label_blacklist_char')
        self.label_blacklist_char.setGeometry(QRect(15, 108, 111, 16))

        # LINE EDIT - Blacklist characters
        self.line_edit_blacklist_char = QLineEdit(self.ocr_tab)
        self.line_edit_blacklist_char.setObjectName('line_edit_blacklist_char')
        self.line_edit_blacklist_char.setGeometry(QRect(130, 105, 196, 22))
        self.line_edit_blacklist_char.textChanged.connect(self.toggle_apply_button)
        self.line_edit_blacklist_char.editingFinished.connect(lambda: SettingsUI.remove_duplicate_chars(self.line_edit_blacklist_char))
        self.line_edits['line_edit_blacklist_char'] = self.line_edit_blacklist_char  # Add to the dictionary

        # CHECKBOX - Enable
        self.checkbox_blacklist_char = QCheckBox(self.ocr_tab)
        self.checkbox_blacklist_char.setObjectName('checkbox_blacklist_char')
        self.checkbox_blacklist_char.setGeometry(QRect(333, 106, 60, 20))
        self.checkbox_blacklist_char.stateChanged.connect(self.toggle_apply_button)
        self.checkbox_blacklist_char.clicked.connect(lambda: self.toggle_whitelist_blacklist_checkbox(self.checkbox_blacklist_char))

        # LABEL - Whitelist characters
        self.label_whitelist_char = QLabel(self.ocr_tab)
        self.label_whitelist_char.setObjectName('label_whitelist_char')
        self.label_whitelist_char.setGeometry(QRect(15, 138, 111, 16))

        # LINE EDIT - Whitelist characters
        self.line_edit_whitelist_char = QLineEdit(self.ocr_tab)
        self.line_edit_whitelist_char.setObjectName('line_edit_whitelist_char')
        self.line_edit_whitelist_char.setGeometry(QRect(130, 136, 196, 22))
        self.line_edit_whitelist_char.textChanged.connect(self.toggle_apply_button)
        self.line_edit_whitelist_char.editingFinished.connect(lambda: SettingsUI.remove_duplicate_chars(self.line_edit_whitelist_char))
        self.line_edits['line_edit_whitelist_char'] = self.line_edit_whitelist_char  # Add to the dictionary

        # CHECKBOX - Enable
        self.checkbox_whitelist_char = QCheckBox(self.ocr_tab)
        self.checkbox_whitelist_char.setObjectName('checkbox_whitelist_char')
        self.checkbox_whitelist_char.setGeometry(QRect(333, 137, 60, 20))
        self.checkbox_whitelist_char.stateChanged.connect(self.toggle_apply_button)
        self.checkbox_whitelist_char.clicked.connect(lambda: self.toggle_whitelist_blacklist_checkbox(self.checkbox_whitelist_char))

        # LABEL - Tesseract Install Path
        self.label_tesseract_install_path = QLabel(self.ocr_tab)
        self.label_tesseract_install_path.setObjectName('label_tesseract_install_path')
        self.label_tesseract_install_path.setGeometry(QRect(15, 180, 160, 16))

        # LINE EDIT - Tesseract Install Path
        self.line_edit_tesseract_install_path = QLineEdit(self.ocr_tab)
        self.line_edit_tesseract_install_path.setObjectName('line_edit_tesseract_install_path')
        self.line_edit_tesseract_install_path.setGeometry(QRect(15, 200, 311, 22))
        self.line_edit_tesseract_install_path.setCursorPosition(0)
        self.line_edit_tesseract_install_path.textChanged.connect(self.toggle_apply_button)
        self.line_edits['line_edit_tesseract_install_path'] = self.line_edit_tesseract_install_path  # Add to the dictionary
        self.line_edit_tesseract_install_path.setText(self.config['ocr']['tesseract_path'])

        # BUTTON - ...
        self.button_tesseract_install_path = QPushButton(self.ocr_tab)
        self.button_tesseract_install_path.setObjectName('button_tesseract_install_path')
        self.button_tesseract_install_path.setGeometry(QRect(330, 198, 24, 24))
        self.button_tesseract_install_path.setAutoDefault(False)
        self.button_tesseract_install_path.clicked.connect(self.select_audio_file)

        self.tab_widget.addTab(self.ocr_tab, '')

        # ======== PREPROCESS TAB ========

        self.preprocess_tab = QWidget()
        self.preprocess_tab.setObjectName('preprocess_tab')

        # LABEL - Scale Factor
        self.label_scale_factor = QLabel(self.preprocess_tab)
        self.label_scale_factor.setObjectName('label_scale_factor')
        self.label_scale_factor.setGeometry(QRect(16, 12, 121, 16))

        # SPINBOX - Scale Factor
        self.spinbox_scale_factor = QDoubleSpinBox(self.preprocess_tab)
        self.spinbox_scale_factor.setObjectName('spinbox_scale_factor')
        self.spinbox_scale_factor.setGeometry(QRect(90, 10, 45, 22))
        self.spinbox_scale_factor.setMinimum(1.0)
        self.spinbox_scale_factor.setMaximum(10.0)
        self.spinbox_scale_factor.setSingleStep(0.1)
        self.spinbox_scale_factor.setDecimals(1)
        self.spinbox_scale_factor.valueChanged.connect(lambda name='spinbox_scale_factor':
                                                       self.toggle_highlight(name))
        self.spinbox_scale_factor.valueChanged.connect(self.toggle_apply_button)
        self.spinbox_scale_factor.editingFinished.connect(self.toggle_apply_button)
        self.spinbox_scale_factor.setFocusPolicy(Qt.NoFocus)

        line_edit_scale_factor = self.spinbox_scale_factor.lineEdit()
        line_edit_scale_factor.installEventFilter(self)
        self.spinboxes['spinbox_scale_factor'] = self.spinbox_scale_factor  # Add to the dictionary

        # CHECKBOX - Grayscale
        self.checkbox_grayscale = QCheckBox(self.preprocess_tab)
        self.checkbox_grayscale.setObjectName('checkbox_grayscale')
        self.checkbox_grayscale.setGeometry(QRect(16, 40, 201, 20))
        self.checkbox_grayscale.stateChanged.connect(self.toggle_apply_button)

        # CHECKBOX - Gaussian Blur
        self.checkbox_gaussian_blur = QCheckBox(self.preprocess_tab)
        self.checkbox_gaussian_blur.setObjectName('checkbox_gaussian_blur')
        self.checkbox_gaussian_blur.setGeometry(QRect(16, 70, 201, 20))
        self.checkbox_gaussian_blur.stateChanged.connect(self.toggle_apply_button)

        # CHECKBOX - Median Blur
        self.checkbox_median_blur = QCheckBox(self.preprocess_tab)
        self.checkbox_median_blur.setObjectName('checkbox_median_blur')
        self.checkbox_median_blur.setGeometry(QRect(130, 70, 201, 20))
        self.checkbox_median_blur.stateChanged.connect(self.toggle_apply_button)

        # CHECKBOX - Remove Noise
        self.checkbox_remove_noise = QCheckBox(self.preprocess_tab)
        self.checkbox_remove_noise.setObjectName('checkbox_remove_noise')
        self.checkbox_remove_noise.setGeometry(QRect(240, 70, 180, 20))
        self.checkbox_remove_noise.stateChanged.connect(self.toggle_apply_button)

        # GROUP BOX - Thresholding
        outer_threshold_widget = QWidget(self.preprocess_tab)
        outer_threshold_widget.setGeometry(0, 90, 409, 71)
        threshold_layout = QHBoxLayout(outer_threshold_widget)
        threshold_group_box = QGroupBox("Thresholding")

        # CHECKBOX - Adaptive
        self.checkbox_adaptive_thresholding = QCheckBox(threshold_group_box)
        self.checkbox_adaptive_thresholding.setObjectName('checkbox_adaptive_thresholding')
        self.checkbox_adaptive_thresholding.setGeometry(QRect(20, 21, 180, 20))
        self.checkbox_adaptive_thresholding.stateChanged.connect(self.toggle_apply_button)

        # SPINBOX - Adaptive Threshold
        self.spinbox_adaptive_threshold = QSpinBox(threshold_group_box)
        self.spinbox_adaptive_threshold.setObjectName('spinbox_adaptive_threshold')
        self.spinbox_adaptive_threshold.setGeometry(QRect(98, 19, 45, 22))
        self.spinbox_adaptive_threshold.setMinimum(1)
        self.spinbox_adaptive_threshold.setMaximum(101)
        self.spinbox_adaptive_threshold.setSingleStep(2)
        self.spinbox_adaptive_threshold.valueChanged.connect(lambda name='spinbox_adaptive_threshold':
                                                             self.toggle_highlight(name))
        self.spinbox_adaptive_threshold.valueChanged.connect(self.toggle_apply_button)
        self.spinbox_adaptive_threshold.editingFinished.connect(self.toggle_apply_button)
        self.spinbox_adaptive_threshold.setFocusPolicy(Qt.NoFocus)

        line_edit_adaptive_threshold = self.spinbox_adaptive_threshold.lineEdit()
        line_edit_adaptive_threshold.installEventFilter(self)
        self.spinboxes['spinbox_adaptive_threshold'] = self.spinbox_adaptive_threshold

        # CHECKBOX - Global
        self.checkbox_global_thresholding = QCheckBox(threshold_group_box)
        self.checkbox_global_thresholding.setObjectName('checkbox_global_thresholding')
        self.checkbox_global_thresholding.setGeometry(QRect(185, 21, 180, 20))
        self.checkbox_global_thresholding.stateChanged.connect(self.toggle_apply_button)

        # SPINBOX - Global Threshold
        self.spinbox_global_threshold = QSpinBox(threshold_group_box)
        self.spinbox_global_threshold.setObjectName('spinbox_global_threshold')
        self.spinbox_global_threshold.setGeometry(QRect(250, 19, 45, 22))
        self.spinbox_global_threshold.setMinimum(0)
        self.spinbox_global_threshold.setMaximum(255)
        self.spinbox_global_threshold.valueChanged.connect(lambda name='spinbox_global_threshold':
                                                           self.toggle_highlight(name))
        self.spinbox_global_threshold.valueChanged.connect(self.toggle_apply_button)
        self.spinbox_global_threshold.editingFinished.connect(self.toggle_apply_button)
        self.spinbox_global_threshold.setFocusPolicy(Qt.NoFocus)

        line_edit_global_threshold = self.spinbox_global_threshold.lineEdit()
        line_edit_global_threshold.installEventFilter(self)
        self.spinboxes['spinbox_global_threshold'] = self.spinbox_global_threshold

        threshold_layout.addWidget(threshold_group_box)

        # GROUP BOX - Structure Manipulation
        outer_structure_manipulation_widget = QWidget(self.preprocess_tab)
        outer_structure_manipulation_widget.setGeometry(0, 150, 409, 71)
        structure_manipulation_layout = QHBoxLayout(outer_structure_manipulation_widget)
        structure_manipulation_group_box = QGroupBox("Structure Manipulation")

        # CHECKBOX - Dilate
        self.checkbox_dilate = QCheckBox("Dilate", structure_manipulation_group_box)
        self.checkbox_dilate.setObjectName('checkbox_dilate')
        self.checkbox_dilate.setGeometry(QRect(20, 21, 180, 20))
        self.checkbox_dilate.stateChanged.connect(self.toggle_apply_button)

        # CHECKBOX - Erode
        self.checkbox_erode = QCheckBox("Erode", structure_manipulation_group_box)
        self.checkbox_erode.setObjectName('checkbox_erode')
        self.checkbox_erode.setGeometry(QRect(90, 21, 180, 20))
        self.checkbox_erode.stateChanged.connect(self.toggle_apply_button)

        self.label_struct_man_kernel = QLabel("Kernel:", structure_manipulation_group_box)
        self.label_struct_man_kernel.setObjectName('label_struct_man_kernel')
        self.label_struct_man_kernel.setGeometry(QRect(150, 23, 121, 16))

        structure_manipulation_layout.addWidget(structure_manipulation_group_box)

        # CHECKBOX - Deskew
        self.checkbox_deskew = QCheckBox(self.preprocess_tab)
        self.checkbox_deskew.setObjectName('checkbox_deskew')
        self.checkbox_deskew.setGeometry(QRect(16, 220, 180, 20))
        self.checkbox_deskew.stateChanged.connect(self.toggle_apply_button)

        self.tab_widget.addTab(self.preprocess_tab, '')

        # ======== OUTPUT TAB ========
        self.output_tab = QWidget()
        self.output_tab.setObjectName('output_tab')

        # CHECKBOX - Copy to clipboard
        self.checkbox_copyto_clipboard = QCheckBox(self.output_tab)
        self.checkbox_copyto_clipboard.setObjectName('checkbox_copy_clipboard')
        self.checkbox_copyto_clipboard.setGeometry(QRect(16, 10, 141, 20))
        self.checkbox_copyto_clipboard.stateChanged.connect(self.toggle_apply_button)

        # CHECKBOX - Show popup window (OCR Text)
        self.checkbox_show_popup_window = QCheckBox(self.output_tab)
        self.checkbox_show_popup_window.setObjectName('checkbox_show_popup_window')
        self.checkbox_show_popup_window.setGeometry(QRect(16, 40, 190, 20))
        self.checkbox_show_popup_window.stateChanged.connect(self.toggle_apply_button)

        # CHECKBOX - Remove empty lines
        self.checkbox_remove_empty_lines = QCheckBox(self.output_tab)
        self.checkbox_remove_empty_lines.setObjectName('checkbox_remove_empty_lines')
        self.checkbox_remove_empty_lines.setGeometry(QRect(16, 70, 190, 20))
        self.checkbox_remove_empty_lines.stateChanged.connect(self.toggle_apply_button)

        # CHECKBOX - Save captured image
        self.checkbox_save_captured_image = QCheckBox(self.output_tab)
        self.checkbox_save_captured_image.setObjectName('checkbox_save_captured_image')
        self.checkbox_save_captured_image.setGeometry(QRect(16, 100, 171, 20))
        self.checkbox_save_captured_image.stateChanged.connect(self.toggle_apply_button)

        # CHECKBOX - Save enhanced image
        self.checkbox_save_enhanced_image = QCheckBox(self.output_tab)
        self.checkbox_save_enhanced_image.setObjectName('checkbox_save_enhanced_image')
        self.checkbox_save_enhanced_image.setGeometry(QRect(16, 130, 171, 20))
        self.checkbox_save_enhanced_image.stateChanged.connect(self.toggle_apply_button)

        # LABEL - Output folder
        self.label_output_folder = QLabel(self.output_tab)
        self.label_output_folder.setObjectName('label_output_folder')
        self.label_output_folder.setGeometry(QRect(15, 163, 81, 16))

        # LINE EDIT - Output folder
        self.line_edit_output_folder = QLineEdit(self.output_tab)
        self.line_edit_output_folder.setObjectName('line_edit_output_folder')
        self.line_edit_output_folder.setGeometry(QRect(95, 161, 251, 22))
        self.line_edit_output_folder.setCursorPosition(0)
        self.line_edit_output_folder.textChanged.connect(self.toggle_apply_button)
        self.line_edits['line_edit_output_folder'] = self.line_edit_output_folder  # Add to the dictionary

        # BUTTON - ...
        self.button_output_folder = QPushButton(self.output_tab)
        self.button_output_folder.setObjectName('button_output_folder')
        self.button_output_folder.setGeometry(QRect(350, 160, 24, 24))
        self.button_output_folder.setAutoDefault(False)
        self.button_output_folder.clicked.connect(self.select_autosave_output_folder)

        self.tab_widget.addTab(self.output_tab, '')

        # ======== TRANSLATE TAB ========
        self.translate_tab = QWidget()
        self.translate_tab.setObjectName('translate_tab')

        # CHECKBOX - Append translation to clipboard
        self.checkbox_append_translation = QCheckBox(self.translate_tab)
        self.checkbox_append_translation.setObjectName('checkbox_append_translation')
        self.checkbox_append_translation.setGeometry(QRect(16, 10, 201, 20))
        self.checkbox_append_translation.stateChanged.connect(self.toggle_apply_button)

        # CHECKBOX - Show translation in popup window
        self.checkbox_show_translation = QCheckBox(self.translate_tab)
        self.checkbox_show_translation.setObjectName('checkbox_show_translation')
        self.checkbox_show_translation.setGeometry(QRect(16, 40, 211, 20))
        self.checkbox_show_translation.stateChanged.connect(self.toggle_apply_button)

        self.table_widget = QTableWidget(self.translate_tab)
        table_header_labels = ["OCR Language", "Translate To (Using Google Translate)"]

        header_horizontal = MyHeader(Qt.Horizontal, self.table_widget)
        self.table_widget.setHorizontalHeader(header_horizontal)

        header_vertical = MyHeader(Qt.Vertical, self.table_widget)
        self.table_widget.setVerticalHeader(header_vertical)

        self.table_widget.setColumnCount(2)
        self.table_widget.setRowCount(110)
        self.table_widget.setHorizontalHeaderLabels(table_header_labels)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Make the entire table read-only
        self.table_widget.setSelectionMode(QAbstractItemView.NoSelection)  # No items can be selected

        self.translate_to_comboboxes = []

        for table_row, combobox_language in enumerate(language_list().values(), start=0):
            table_widget_language = QTableWidgetItem(combobox_language.capitalize())

            translate_to_combobox = QComboBox()
            # Add the languages with the first letter capitalized to the combo box, excluding the current language
            for language_code, language_name in language_list().items():

                if language_name != combobox_language:
                    translate_to_combobox.addItem(language_name.capitalize())

                if language_code == self.config['translate'][combobox_language.lower()]:
                    index = translate_to_combobox.findText(language_name.capitalize())

                    if index >= 0:  # -1 means the text was not found
                        translate_to_combobox.setCurrentIndex(index)

            self.table_widget.setItem(table_row, 0, table_widget_language)
            self.table_widget.setCellWidget(table_row, 1, translate_to_combobox)
            self.translate_to_comboboxes.append(translate_to_combobox)
            translate_to_combobox.currentIndexChanged.connect(self.toggle_apply_button)

        # Make 'Translate To' column stretch to fill table width.
        header_horizontal.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_horizontal.setSectionResizeMode(1, QHeaderView.Stretch)

        self.table_widget.setObjectName('table_widget')
        self.table_widget.setGeometry(QRect(5, 70, 399, 189))
        self.table_widget.verticalHeader().setVisible(False)

        self.tab_widget.addTab(self.translate_tab, '')
        self.tab_widget.setCurrentIndex(0)

        # Connect the focus events to custom slots for all QLineEdit widgets
        for line_edit in self.line_edits.values():
            line_edit.installEventFilter(self)

        self.init_ui()

    def init_ui(self):
        self.button_apply_settings.setText("Apply")
        self.button_OK_settings.setText("OK")
        self.button_cancel_settings.setText("Cancel")

        # Tab 0
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.preferences_tab), "Preferences")
        self.checkbox_minimize_to_sys_tray.setText("Minimize to system tray on close")
        self.checkbox_play_sound.setText("Play sound on capture")
        self.label_sound_file.setText("Sound file:")
        self.button_sound_file.setText(". . .")

        # Tab 1
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.ocr_tab), "OCR")
        self.label_ocr_language.setText("OCR Languages:")
        self.button_ocr_language.setText("Show")
        self.label_psm_value.setText("Page segment mode:")
        self.label_oem_value.setText("OCR Engine mode:")
        self.combobox_oem_value.setItemText(0, "0")
        self.combobox_oem_value.setItemText(1, "1")
        self.combobox_oem_value.setItemText(2, "2")
        self.combobox_oem_value.setItemText(3, "3")
        self.checkbox_preserve_interword_spaces.setText("Preserve interword spaces")
        self.checkbox_preserve_interword_spaces.setToolTip("Enable this option to preserve interword spaces in the OCR output.\n"
                                                           "This helps maintain the original spacing between words in the recognized text.")
        self.label_blacklist_char.setText("Blacklist characters:")
        self.label_whitelist_char.setText("Whitelist characters:")
        self.checkbox_blacklist_char.setText("Enable")
        self.checkbox_whitelist_char.setText("Enable")
        self.label_tesseract_install_path.setText("Tesseract Installation Path:")
        self.button_tesseract_install_path.setText(". . .")

        # Tab 2
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.preprocess_tab), "Preprocess")
        self.label_scale_factor.setText("Scale Factor:")
        self.checkbox_grayscale.setText("Grayscale")
        self.checkbox_gaussian_blur.setText("Gaussian Blur")
        self.checkbox_median_blur.setText("Median Blur")
        self.checkbox_remove_noise.setText("Remove Noise")
        self.checkbox_adaptive_thresholding.setText("Adaptive:")
        self.checkbox_global_thresholding.setText("Global:")
        self.checkbox_global_thresholding.setToolTip("Enable this option to convert the image to a binary format.\n"
                                                     "Binarization simplifies the image by separating pixels into black\n"
                                                     "and white, making it suitable for various image processing tasks.")
        self.spinbox_global_threshold.setToolTip("Threshold minimum = 0, maximum = 255\n"
                                                 "Set the threshold value for binarization. Pixels with values above\n"
                                                 "this threshold will be set to white, and those below will be black.\n"
                                                 "Adjust the threshold based on the characteristics of your image.")
        self.checkbox_deskew.setText("Deskew")
        self.checkbox_deskew.setToolTip("Enable this option to automatically straighten skewed text in the image.\n"
                                        "Improved alignment enhances OCR accuracy, making text extraction\n"
                                        "more efficient. Ideal for scanned document or image with tilted text.")

        # Tab 3
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.output_tab), "Output")
        self.checkbox_copyto_clipboard.setText("Copy to clipboard")
        self.checkbox_show_popup_window.setText("Show popup window (OCR Text)")
        self.checkbox_remove_empty_lines.setText("Remove empty lines in OCR text")
        self.checkbox_save_captured_image.setText("Save captured image")
        self.checkbox_save_enhanced_image.setText("Save enhanced image")
        self.label_output_folder.setText("Output folder:")
        self.button_output_folder.setText(". . .")

        # Tab 4
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.translate_tab), "Translate")
        self.checkbox_append_translation.setText("Append translation to clipboard")
        self.checkbox_show_translation.setText("Show translation in popup window")

    def toggle_checkbox_psm_tooltip(self, psm_value):
        psm_tooltip_text = {
            0: "Fully automatic page segmentation, but\nno OSD. (Default)",
            1: "Assume a single column of text of variable sizes. ",
            2: "Assume a single uniform block of vertically\naligned text. ",
            3: "Assume a single uniform block of text. ",
            4: "Treat the image as a single text line. ",
            5: "Treat the image as a single word. ",
            6: "Treat the image as a single word in a circle. ",
            7: "Treat the image as a single character. ",
            8: "Sparse text. Find as much text as possible in\nno particular order. ",
            9: "Raw line. Treat the image as a single text line,\nbypassing hacks that are Tesseract-specific."
        }
        self.combobox_psm_value.setToolTip(psm_tooltip_text.get(psm_value, ''))

    def toggle_checkbox_oem_tooltip(self, oem_value):
        oem_tooltip_text = {
            0: "Legacy engine only.",
            1: "Neural nets LSTM engine only.",
            2: "Legacy + LSTM engines.",
            3: "Default, based on what is available."
        }
        self.combobox_oem_value.setToolTip(oem_tooltip_text.get(oem_value, ''))

    def toggle_highlight(self, name):
        logger.info(f"SetStyleSheet for {name}")
        self.spinboxes[name].lineEdit().setStyleSheet("""QLineEdit {
                                                selection-background-color: white;
                                                selection-color: black
                                                }""")

    def initialize_settings_components(self):
        logger.info("Initializing settings component")
        self.config = load_config()
        self.initialize_settings_components_finish = False
        self.set_widget_value(self.checkbox_minimize_to_sys_tray, 'preferences', 'minimize_to_system_tray')
        self.set_widget_value(self.checkbox_play_sound, 'preferences', 'enable_sound')
        self.set_widget_value(self.line_edit_sound_file, 'preferences', 'sound_file', True)
        self.set_widget_value(self.checkbox_preserve_interword_spaces, 'ocr', 'preserve_interword_spaces')
        self.set_widget_value(self.spinbox_scale_factor, 'preprocess', 'scale_factor')
        self.set_widget_value(self.checkbox_gaussian_blur, 'preprocess', 'gaussian_blur')
        self.set_widget_value(self.checkbox_median_blur, 'preprocess', 'median_blur')
        self.set_widget_value(self.checkbox_remove_noise, 'preprocess', 'remove_noise')
        self.set_widget_value(self.checkbox_adaptive_thresholding, 'preprocess', 'adaptive_thresholding')
        self.set_widget_value(self.checkbox_global_thresholding, 'preprocess', 'global_thresholding')
        self.set_widget_value(self.spinbox_global_threshold, 'preprocess', 'global_threshold')
        self.set_widget_value(self.checkbox_deskew, 'preprocess', 'deskew')
        self.set_widget_value(self.line_edit_blacklist_char, 'ocr', 'blacklist_char')
        self.set_widget_value(self.line_edit_whitelist_char, 'ocr', 'whitelist_char')
        self.set_widget_value(self.checkbox_blacklist_char, 'ocr', 'enable_blacklist_char')
        self.set_widget_value(self.checkbox_whitelist_char, 'ocr', 'enable_whitelist_char')
        self.set_widget_value(self.checkbox_copyto_clipboard, 'output', 'copy_to_clipboard')
        self.set_widget_value(self.checkbox_show_popup_window, 'output', 'show_popup_window')
        self.set_widget_value(self.checkbox_remove_empty_lines, 'output', 'remove_empty_lines')
        self.set_widget_value(self.checkbox_save_captured_image, 'output', 'save_captured_image')
        self.set_widget_value(self.checkbox_save_enhanced_image, 'output', 'save_enhanced_image')
        self.set_widget_value(self.line_edit_output_folder, 'output', 'output_folder_path', True)
        self.set_widget_value(self.checkbox_show_translation, 'translate', 'enable_translation')
        self.open_file_dialog_path = self.config['preferences']['sound_file']
        self.open_folder_dialog_path = self.config['output']['output_folder_path']
        self.initialize_settings_components_finish = True

    def set_widget_value(self, widget, table_name, key, line_edit_replace=None):
        value = self.config[table_name][key]
        try:
            if line_edit_replace:
                formatted_value = re.sub(r'\\+', r'\\', str(value).replace('/', '\\'))
                widget.setText(formatted_value)
            elif isinstance(widget, QLineEdit):
                widget.setText(value)
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(value)
        except (TypeError, ValueError, AttributeError):
            logger.error(f"Invalid configuration - Table: {table_name} | Key: {key} | Value: {value}")

    def eventFilter(self, obj, event):
        # Clear the stylesheet when a mouse button is pressed inside the QLineEdit of any spin box
        for spinbox in self.spinboxes.values():
            if obj == spinbox.lineEdit() and event.type() == QEvent.MouseButtonPress:
                logger.info("SPINBOX HIGHLIGHTED")
                spinbox.lineEdit().setStyleSheet("")

        for object_name, line_edit in self.line_edits.items():
            if obj is line_edit:
                if event.type() == QEvent.MouseButtonPress:
                    # Handle focus in event (mouse clicks inside)
                    obj.setStyleSheet("border: 1px solid rgb(31, 136, 218);")
                elif event.type() == QEvent.FocusOut:
                    # Handle focus out event (mouse clicks outside)
                    line_edit.clearFocus()
                    line_edit.setStyleSheet("border: 1px solid rgb(115, 115, 115);")

        return super().eventFilter(obj, event)

    def toggle_ocr_tab_widgets_display(self):
        ocr_tab_widgets = self.ocr_tab.findChildren(QWidget)
        scroll_area_widgets = self.scroll_area.findChildren(QWidget)
        language_widgets = [self.label_ocr_language, self.button_ocr_language]

        self.check_language_file()

        for widget in ocr_tab_widgets:
            if widget in language_widgets or widget in scroll_area_widgets:
                continue
            widget.hide() if not self.ocr_tab_hide_widgets else widget.show()

        if not self.ocr_tab_hide_widgets:
            self.button_ocr_language.setText("Hide")
            self.scroll_area.setVisible(True)
        else:
            self.button_ocr_language.setText("Show")
            self.scroll_area.setVisible(False)

        self.ocr_tab_hide_widgets = not self.ocr_tab_hide_widgets

    def check_language_file(self):
        for language_code, language_name in language_set().items():
            file_path = Path('./tessdata') / f'{language_code}.traineddata'
            if file_path.exists():
                if language_code in self.config['ocr']['language']:
                    self.sc_checkbox_dict[f'{language_name}'].setChecked(True)
                else:
                    self.sc_checkbox_dict[f'{language_name}'].setChecked(False)
                self.sc_checkbox_dict[f'{language_name}'].setEnabled(True)
                self.sc_button_dict[f'{language_name}'].setVisible(False)
            else:
                self.sc_checkbox_dict[f'{language_name}'].setChecked(False)
                self.sc_checkbox_dict[f'{language_name}'].setEnabled(False)
                self.sc_button_dict[f'{language_name}'].setVisible(True)

    def download_from_github(self):
        sender_button = self.sender()
        label = None

        for name, button in self.sc_button_dict.items():
            if button is sender_button:
                label = name
                break

        for language_code, language_name in language_set().items():
            if label == language_name:
                tessdata_folder = Path("./tessdata/")
                file_name = f'{language_code}.traineddata'
                download_url = f'https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/{file_name}'
                download_destination = f'{tessdata_folder}/{file_name}.tmp'
                tessdata_folder.mkdir(parents=True, exist_ok=True)

                self.widget_language_name = language_name
                self.sc_progressbar_dict[f'{self.widget_language_name}'].setVisible(True)
                self.sc_button_dict[f'{self.widget_language_name}'].setVisible(False)
                self.button_ocr_language.setEnabled(False)

                self.download_thread = DownloadThread(download_url, str(download_destination), file_name)
                self.download_thread.progress_signal.connect(self.update_progress_bar)
                self.download_thread.error_signal.connect(self.handle_download_error)
                self.download_thread.start()

                # Start a separate thread to periodically check for internet connectivity during the download
                self.check_internet_thread = QThread(self)
                self.check_internet_thread.run = self.check_internet_connection
                self.check_internet_thread.start()

    def update_progress_bar(self, value):
        self.sc_progressbar_dict[f'{self.widget_language_name}'].setValue(value)
        if value == 100:
            self.button_ocr_language.setEnabled(True)
            self.sc_progressbar_dict[f'{self.widget_language_name}'].setVisible(False)
            self.sc_checkbox_dict[f'{self.widget_language_name}'].setEnabled(True)
            self.scroll_area.update()
            logger.info("Download 100%!")

    def handle_download_error(self, error_message):
        self.reset_download_button()
        logger.error(f"Download failed: {error_message}")

    def check_internet_connection(self):
        while not self.download_thread._stop_event:
            time.sleep(1)
            if not self.download_thread.is_internet_available():
                # If internet connection is lost during download, stop the download thread
                self.download_thread.stop_download()
                self.reset_download_button()
                logger.error("Internet connection lost. Download aborted.")
                break

    def reset_download_button(self):
        self.button_ocr_language.setEnabled(True)
        self.sc_button_dict[f'{self.widget_language_name}'].setVisible(True)
        self.sc_progressbar_dict[f'{self.widget_language_name}'].setVisible(False)

    @staticmethod
    def remove_duplicate_chars(line_edit):
        text = line_edit.text()
        unique_chars = ''.join(sorted(set(text)))
        line_edit.blockSignals(True)
        line_edit.setText(unique_chars)
        line_edit.blockSignals(False)

    def toggle_whitelist_blacklist_checkbox(self, clicked_checkbox):
        target_checkbox = self.checkbox_blacklist_char if clicked_checkbox == self.checkbox_whitelist_char else self.checkbox_whitelist_char
        target_checkbox.setChecked(False)

    def select_audio_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", self.open_file_dialog_path,
                                                   "Audio Files (*.mp3 *.wav)", options=options)
        if file_path:
            formatted_file_path = file_path.replace('/', '\\')
            self.line_edit_sound_file.setText(formatted_file_path)
            self.open_file_dialog_path = formatted_file_path

    def select_autosave_output_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", self.open_folder_dialog_path)
        if folder_path:
            formatted_folder_path = folder_path.replace('/', '\\')
            self.line_edit_output_folder.setText(formatted_folder_path)
            self.open_folder_dialog_path = formatted_folder_path

    def toggle_apply_button(self):
        if not self.initialize_settings_components_finish:
            return
        if not self.button_apply_was_enabled:
            self.fade_timer.start()
            self.button_apply_settings.setEnabled(True)
            logger.info(f"Fade timer start: Apply button state: {self.button_apply_was_enabled}")

    def update_apply_button_state(self):
        self.button_apply_was_enabled = True
        # Gradually change the Apply button text color to make it visible
        current_color = self.button_apply_settings.palette().color(QPalette.ButtonText)
        target_color = QColor(0, 0, 0)  # Black text color
        if current_color != target_color:
            new_color = QColor()
            for i in range(3):
                new_color.setRed(int(current_color.red() + ((target_color.red() - current_color.red()) / 10)))
                new_color.setGreen(int(current_color.green() + ((target_color.green() - current_color.green()) / 10)))
                new_color.setBlue(int(current_color.blue() + ((target_color.blue() - current_color.blue()) / 10)))

            palette = QPalette()
            palette.setColor(QPalette.ButtonText, new_color)
            self.button_apply_settings.setPalette(palette)
        else:
            # Stop the timer when the desired color is reached
            logger.info(f"Fade timer stop: Apply button state: {self.button_apply_was_enabled}")
            self.fade_timer.stop()

    def stop_updating_apply_button(self):
        logger.info(f"Apply button state: {self.button_apply_was_enabled}")
        if self.button_apply_was_enabled:
            self.fade_timer.stop()  # Forcefully stop the update_apply_button_state
            palette = QPalette()
            gray_color = QColor(128, 128, 128)
            palette.setColor(QPalette.ButtonText, gray_color)
            self.button_apply_settings.setPalette(palette)
            self.button_apply_settings.setEnabled(False)
            self.button_apply_was_enabled = False
            logger.info(f"Apply button state: {self.button_apply_was_enabled}")

    def apply_button_clicked(self):
        try:
            self.button_OK_settings.setDefault(False)
            self.check_sound_file()
            self.check_and_create_output_folder()
            self.button_OK_settings.setFocus()

        except ValueError as e:
            show_message_box("Critical", "Error", str(e))
        else:
            if self.output_folder_created:
                self.stop_updating_apply_button()

    def ok_button_clicked(self):
        try:
            self.check_sound_file()
            self.check_and_create_output_folder()

        except ValueError as e:
            show_message_box("Critical", "Error", str(e))
        else:
            if self.output_folder_created:
                self.stop_updating_apply_button()
                self.hide()

    def check_sound_file(self):
        if self.checkbox_play_sound.isChecked():
            if not self.line_edit_sound_file.text():
                raise ValueError("Sound file is empty.")
            if not Path(self.line_edit_sound_file.text()).exists():
                raise ValueError(f"Sound file does not exist.")

    def check_and_create_output_folder(self):
        output_folder_path = self.fix_path(self.line_edit_output_folder)
        self.line_edit_output_folder.setText(output_folder_path)

        if not output_folder_path:
            if self.checkbox_save_captured_image.isChecked() or self.checkbox_save_enhanced_image.isChecked():
                self.tab_widget.setCurrentIndex(3)
                raise ValueError("Output folder is empty.")

        if Path(output_folder_path).exists() and Path(output_folder_path).is_dir():
            logger.info(f"Output folder already exist '{output_folder_path}'")
            self.output_folder_created = True
            self.save_settings_config()
            return

        self.tab_widget.setCurrentIndex(3)
        response = show_message_box(
            "Question",
            "Confirm",
            "Output Folder \"" + output_folder_path + "\" does not exist.\n\nDo you want to create it?",
        )
        if response == "No":
            self.output_folder_created = False
            return

        drive_letter = Path(output_folder_path).drive

        if not Path(drive_letter).exists():
            logger.error(f"Failed to create output folder. Drive letter does not exist.")
            raise ValueError("Failed to create output folder. Drive letter does not exist.")
        try:
            logger.info(f"Creating output folder")
            Path(output_folder_path).mkdir(parents=True, exist_ok=True)
            self.output_folder_created = True
            logger.success(f"Output folder created successfully '{output_folder_path}'")
            self.save_settings_config()

        except Exception as e:
            logger.error(f"Failed to create output folder: {e}")
            raise ValueError("Failed to create output folder.")

    def save_settings_config(self):
        settings_config = {
            "preferences": {
                'minimize_to_system_tray': self.checkbox_minimize_to_sys_tray.isChecked(),
                'enable_sound': self.checkbox_play_sound.isChecked(),
                'sound_file': self.fix_path(self.line_edit_sound_file)
            },
            "ocr": {
                'page_segmentation_mode': int(self.combobox_psm_value.currentText()),
                'ocr_engine_mode': int(self.combobox_oem_value.currentText()),
                'preserve_interword_spaces': self.checkbox_preserve_interword_spaces.isChecked(),
                'enable_blacklist_char': self.checkbox_blacklist_char.isChecked(),
                'blacklist_char': self.line_edit_blacklist_char.text(),
                'enable_whitelist_char': self.checkbox_whitelist_char.isChecked(),
                'whitelist_char': self.line_edit_whitelist_char.text(),

            },
            "preprocess": {
                'scale_factor': self.spinbox_scale_factor.value(),
                'grayscale': self.checkbox_grayscale.isChecked(),
                'gaussian_blur': self.checkbox_gaussian_blur.isChecked(),
                'median_blur': self.checkbox_median_blur.isChecked(),
                'remove_noise': self.checkbox_remove_noise.isChecked(),
                'adaptive_thresholding': self.checkbox_adaptive_thresholding.isChecked(),
                'global_thresholding': self.checkbox_global_thresholding.isChecked(),
                'global_threshold': self.spinbox_global_threshold.value(),
                'deskew': self.checkbox_deskew.isChecked(),
            },
            "output": {
                'copy_to_clipboard': self.checkbox_copyto_clipboard.isChecked(),
                'show_popup_window': self.checkbox_show_popup_window.isChecked(),
                'remove_empty_lines': self.checkbox_remove_empty_lines.isChecked(),
                'save_captured_image': self.checkbox_save_captured_image.isChecked(),
                'save_enhanced_image': self.checkbox_save_enhanced_image.isChecked(),
                'output_folder_path': self.fix_path(self.line_edit_output_folder)
            },
            "translate": {
                'enable_translation': self.checkbox_show_translation.isChecked()
            }
        }
        # Save checked OCR languages
        save_lang = ""
        for language_code, language_name in language_set().items():
            if self.sc_checkbox_dict[f'{language_name}'].isChecked():
                file_path = Path('./tessdata') / f'{language_code}.traineddata'
                if file_path.exists():
                    save_lang = f"{save_lang}+{language_code}" if save_lang else language_code
        settings_config['ocr']['language'] = f'{save_lang}'

        # Get selected language in every Translate To combobox
        for count, language_name in enumerate(language_list().values(), start=0):
            for language_code, name in language_list().items():
                if name == self.translate_to_comboboxes[count].currentText().lower():
                    settings_config['translate'][f'{language_name}'] = f'{language_code}'

        self.check_language_file()
        logger.info("Saving settings in configuration file")
        update_config(settings_config)

    @staticmethod
    def fix_path(line_edit: QLineEdit):
        return re.sub(r'\\+', r'\\', str(line_edit.text()).replace('/', '\\'))

    def cancel_button(self):
        self.close()

    def closeEvent(self, event):
        self.stop_updating_apply_button()
        # For on_settings_ui_closed in MainUI, for disabling 'Show PyTextractOCR' menu in system tray
        # self.finished.emit(0)
        self.close()
        logger.info("Settings window closed")


# For Table Widget
class MyHeader(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def paintSection(self, painter: QPainter, rect: QRect, index: int) -> None:
        painter.setFont(self.font())
        super().paintSection(painter, rect, index)


class DownloadThread(QThread):
    progress_signal = Signal(int)
    error_signal = Signal(str)

    def __init__(self, url, destination, filename):
        super().__init__()
        self.url = url
        self.destination = destination
        self.filename = filename
        self._stop_event = False

    def run(self):
        try:
            with requests.get(self.url, stream=True) as response:
                response.raise_for_status()  # Status code 200 = successful
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0

                with open(self.destination, 'wb') as file:
                    for data in response.iter_content(chunk_size=1024):
                        if self._stop_event:
                            break
                        file.write(data)
                        downloaded_size += len(data)
                        progress_percentage = int(downloaded_size / total_size * 100)
                        self.progress_signal.emit(progress_percentage)

            logger.success(f"Download successful")
            self.rename_downloaded_file()

        except requests.exceptions.RequestException as e:
            self.error_signal.emit(str(e))

    def is_internet_available(self):
        try:
            logger.info("Checking internet connection")
            request.urlopen("http://www.google.com", timeout=5)
            return True

        except (error.URLError, socket.timeout):
            return False

    def rename_downloaded_file(self):
        tessdata_folder = Path('./tessdata')
        current_file_path = tessdata_folder / f'{self.filename}.tmp'
        new_file_path = tessdata_folder / self.filename
        try:
            shutil.move(current_file_path, new_file_path)
            logger.info(f"The file '{current_file_path}' has been renamed to '{new_file_path}'.")

        except Exception as e:
            logger.error(f"Failed to rename the file {current_file_path}: {e}")

        self.stop_download()

    def stop_download(self):
        self._stop_event = True  # Flag to stop the download thread



