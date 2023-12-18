# Standard libraries
import re
from pathlib import Path

# Third-party libraries
from loguru import logger
from PySide6.QtCore import Qt, QRect, QTimer, QEvent
from PySide6.QtGui import QColor, QPalette, QIcon, QPainter
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog,
                               QDoubleSpinBox, QFileDialog, QHeaderView, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QProgressBar, QScrollArea,
                               QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout,
                               QWidget, QGroupBox)

# Custom libraries
from src.config.config import load_config, update_config
from src.ocr.ocr_processor import tesseract_check, tesseract_version
from src.ui.asset_manager import app_icon
from src.utils.message_box import show_message_box
from src.utils.translate import language_list, language_set
from src.ui.download import DownloadTrainedData


class SettingsUI(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings")
        self.setFixedSize(434, 334)
        self.setWindowIcon(QIcon(app_icon))
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowTitleHint)

        self.initialize_settings_components_finish = False
        self.apply_button_was_enabled = False
        self.ocr_tab_widget_visible = False
        self.output_folder_created = True
        self.open_file_dialog_path = None
        self.open_folder_dialog_path = None
        self.open_executable_dialog_path = None

        # Download Trained Data instance
        self.download_trained_data = DownloadTrainedData(self)

        # Dictionary to store QLineEdit and QSpinBox widgets
        self.line_edits = {}
        self.spinboxes = {}

        self.config = load_config()

        # Initialize timer for fading effect
        self.apply_button_state_timer = QTimer()
        self.apply_button_state_timer.setInterval(100)  # Adjust the interval for a smoother transition
        self.apply_button_state_timer.timeout.connect(self.update_apply_button)

        self.horizontal_layout_widget = QWidget(self)
        self.horizontal_layout_widget.setObjectName('horizontal_layout_widget')
        self.horizontal_layout_widget.setGeometry(QRect(180, 300, 244, 31))

        self.horizontal_buttons_layout = QHBoxLayout(self.horizontal_layout_widget)
        self.horizontal_buttons_layout.setObjectName('horizontal_buttons_layout')
        self.horizontal_buttons_layout.setContentsMargins(0, 0, 0, 0)

        # BUTTON - Apply
        self.button_apply_settings = QPushButton("Apply", self.horizontal_layout_widget)
        self.button_apply_settings.setObjectName('button_apply_settings')
        self.button_apply_settings.setEnabled(False)
        self.button_apply_settings.setAutoDefault(False)
        palette = QPalette()
        palette.setColor(QPalette.ButtonText, QColor(128, 128, 128))  # Gray color
        self.button_apply_settings.setPalette(palette)
        self.button_apply_settings.clicked.connect(self.apply_button_clicked)
        self.horizontal_buttons_layout.addWidget(self.button_apply_settings)

        # BUTTON - OK
        self.button_OK_settings = QPushButton("OK", self.horizontal_layout_widget)
        self.button_OK_settings.setObjectName('button_OK_settings')
        self.button_OK_settings.setAutoDefault(True)
        self.button_OK_settings.clicked.connect(self.ok_button_clicked)
        self.horizontal_buttons_layout.addWidget(self.button_OK_settings)

        # BUTTON - Cancel
        self.button_cancel_settings = QPushButton("Cancel", self.horizontal_layout_widget)
        self.button_cancel_settings.setObjectName('button_cancel_settings')
        self.button_cancel_settings.setAutoDefault(False)
        self.button_cancel_settings.clicked.connect(self.cancel_button_clicked)
        self.horizontal_buttons_layout.addWidget(self.button_cancel_settings)

        # ======== TAB WIDGET ========

        self.settings_tab_widget = QTabWidget(self)
        self.settings_tab_widget.setObjectName('tab_widget')
        self.settings_tab_widget.setGeometry(QRect(10, 8, 415, 291))

        # ======== PREFERENCES TAB ========

        self.preferences_tab = QWidget()
        self.preferences_tab.setObjectName('preferences_tab')
        self.settings_tab_widget.addTab(self.preferences_tab, "Preferences")

        self.checkbox_minimize_to_sys_tray = self.create_checkbox("Minimize to system tray on close", self.preferences_tab,
                                                                  'checkbox_minimize_to_sys_tray', (16, 10, 210, 20))

        self.checkbox_play_sound = self.create_checkbox("Play sound on capture", self.preferences_tab, 'checkbox_play_sound', (16, 40, 141, 20))

        self.label_sound_file = self.create_label("Sound file:", self.preferences_tab, 'label_sound_file', (15, 73, 81, 16))

        self.line_edit_sound_file = self.create_line_edit(self.preferences_tab, 'line_edit_sound_file', (95, 71, 251, 22), lambda: 0)

        self.button_sound_file = self.create_button(". . .", self.preferences_tab, 'button_sound_file', (350, 70, 24, 24), False,
                                                    self.select_audio_file)

        # ======== OCR TAB ========

        self.ocr_tab = QWidget()
        self.ocr_tab.setObjectName('ocr_tab')
        self.settings_tab_widget.addTab(self.ocr_tab, "OCR")

        self.label_ocr_language = self.create_label("OCR Languages:", self.ocr_tab, 'label_ocr_language', (15, 16, 90, 16))

        self.button_ocr_language = self.create_button("Show", self.ocr_tab, 'button_ocr_language', (111, 12, 86, 24), False,
                                                      self.ocr_button_clicked_toggle_widgets_display)

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

        self.sc_checkbox_dict = {}
        self.sc_button_dict = {}
        self.sc_progressbar_dict = {}
        self.sc_checkboxes = []

        # Add checkboxes for different languages with "Download" button
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

        self.label_page_seg_mode = self.create_label("Page segment mode:", self.ocr_tab, 'label_page_seg_mode', (15, 48, 119, 16))

        # COMBOBOX - Page segmentation mode
        self.combobox_page_seg_mode = QComboBox(self.ocr_tab)
        self.combobox_page_seg_mode.setObjectName('combobox_page_seg_mode')
        self.combobox_page_seg_mode.setGeometry(QRect(135, 45, 61, 22))
        self.psm_tooltip = {
            3: "Fully automatic page segmentation, but\nno OSD. (Default)",
            4: "Assume a single column of text of variable sizes. ",
            5: "Assume a single uniform block of vertically\naligned text. ",
            6: "Assume a single uniform block of text. ",
            7: "Treat the image as a single text line. ",
            8: "Treat the image as a single word. ",
            9: "Treat the image as a single word in a circle. ",
            10: "Treat the image as a single character. ",
            11: "Sparse text. Find as much text as possible in\nno particular order. ",
            13: "Raw line. Treat the image as a single text line,\nbypassing hacks that are Tesseract-specific."
        }
        for index, tooltip in self.psm_tooltip.items():
            self.combobox_page_seg_mode.addItem(str(index))
        try:
            psm_value = int(self.config['ocr']['page_segmentation_mode'])
            if psm_value < 3 or psm_value == 12 or psm_value > 13:
                self.combobox_page_seg_mode.setCurrentIndex(0)
            else:
                self.combobox_page_seg_mode.setCurrentText(str(psm_value))
        except ValueError as e:
            logger.error(f"Error converting psm value to integer: {e}")
        self.combobox_page_seg_mode.currentIndexChanged.connect(lambda: (self.update_combobox_psm_tooltip(), self.toggle_apply_button()))

        self.label_ocr_engine_mode = self.create_label("OCR Engine mode:", self.ocr_tab, 'label_ocr_engine_mode', (222, 48, 101, 16))

        # COMBOBOX - OCR Engine mode
        self.combobox_ocr_engine_mode = QComboBox(self.ocr_tab)
        self.combobox_ocr_engine_mode.setObjectName('combobox_ocr_engine_mode')
        self.combobox_ocr_engine_mode.setGeometry(QRect(330, 45, 61, 22))
        self.combobox_ocr_engine_mode.addItems(['0', '1', '2', '3'])
        self.oem_tooltip = {
            0: "Legacy engine only.",
            1: "Neural nets LSTM engine only.",
            2: "Legacy + LSTM engines.",
            3: "Default, based on what is available."
        }
        try:
            oem_value = int(self.config['ocr']['ocr_engine_mode'])
            valid_oem_value = max(0, min(oem_value, 3))
            self.combobox_ocr_engine_mode.setCurrentIndex(valid_oem_value)
        except ValueError as e:
            logger.error(f"Error converting oem value to integer: {e}")
        self.combobox_ocr_engine_mode.currentIndexChanged.connect(lambda: (self.update_combobox_oem_tooltip(), self.toggle_apply_button()))

        self.checkbox_pres_iw_spc = self.create_checkbox("Preserve interword spaces", self.ocr_tab, 'checkbox_pres_iw_spc', (16, 75, 171, 20),
                                                         tooltip="Enable this option to preserve interword spaces in the OCR output.\n"
                                                                 "This helps maintain the original spacing between words in the "
                                                                 "recognized text.", )

        self.label_tesseract_version = self.create_label("Tesseract Version: Not found", self.ocr_tab, 'label_tesseract_version', (15, 180, 250, 16))
        self.label_blacklist_char = self.create_label("Blacklist characters:", self.ocr_tab, 'label_blacklist_char', (15, 108, 111, 16))
        self.label_whitelist_char = self.create_label("Whitelist characters:", self.ocr_tab, 'label_whitelist_char', (15, 138, 111, 16))

        self.line_edit_blacklist_char = self.create_line_edit(self.ocr_tab, 'line_edit_blacklist_char', (130, 105, 196, 22),
                                                              lambda: SettingsUI.remove_duplicate_chars(self.line_edit_blacklist_char))
        self.line_edit_whitelist_char = self.create_line_edit(self.ocr_tab, 'line_edit_whitelist_char', (130, 136, 196, 22),
                                                              lambda: SettingsUI.remove_duplicate_chars(self.line_edit_whitelist_char))
        self.line_edit_tesseract_path = self.create_line_edit(self.ocr_tab, 'line_edit_tesseract_path', (15, 200, 311, 22), lambda: 0)

        self.checkbox_blacklist_char = self.create_checkbox("Enable", self.ocr_tab, 'checkbox_blacklist_char', (333, 106, 60, 20),
                                                            lambda: self.toggle_whitelist_blacklist_checkbox(self.checkbox_blacklist_char))
        self.checkbox_whitelist_char = self.create_checkbox("Enable", self.ocr_tab, 'checkbox_whitelist_char', (333, 137, 60, 20),
                                                            lambda: self.toggle_whitelist_blacklist_checkbox(self.checkbox_whitelist_char))

        self.button_tesseract_path = self.create_button(". . .", self.ocr_tab, 'button_tesseract_path', (330, 198, 24, 24), False,
                                                        self.select_tesseract_executable_file)

        # ======== PREPROCESS TAB ========

        self.preprocess_tab = QWidget()
        self.preprocess_tab.setObjectName('preprocess_tab')
        self.settings_tab_widget.addTab(self.preprocess_tab, "Preprocess")

        self.checkbox_enable_preprocess = self.create_checkbox("Enable Preprocess", self.preprocess_tab, 'checkbox_enable_preprocess', (16, 10, 201, 20))

        # Scale Factor
        self.label_scale_factor = self.create_label("Scale Factor:", self.preprocess_tab, 'label_scale_factor', (16, 47, 121, 16))
        self.spinbox_scale_factor = QDoubleSpinBox(self.preprocess_tab)
        self.spinbox_scale_factor.setObjectName('spinbox_scale_factor')
        self.spinbox_scale_factor.setGeometry(QRect(90, 46, 45, 20))
        self.spinbox_scale_factor.setMinimum(1.0)
        self.spinbox_scale_factor.setMaximum(10.0)
        self.spinbox_scale_factor.setSingleStep(0.1)
        self.spinbox_scale_factor.setDecimals(1)
        self.spinbox_scale_factor.valueChanged.connect(lambda value, name='spinbox_scale_factor':
                                                       (self.disable_spinbox_highlight(value, name),
                                                        self.toggle_apply_button()))
        self.spinbox_scale_factor.editingFinished.connect(self.toggle_apply_button)
        self.spinbox_scale_factor.lineEdit().installEventFilter(self)
        self.spinboxes['spinbox_scale_factor'] = self.spinbox_scale_factor  # Add to the dictionary

        self.checkbox_deskew = self.create_checkbox("Deskew", self.preprocess_tab, 'checkbox_deskew', (160, 10, 180, 20),
                                                    tooltip="Enable this option to automatically straighten skewed text in the image.\n"
                                                            "Improved alignment enhances OCR accuracy, making text extraction\n"
                                                            "more efficient. Ideal for scanned document or image with tilted text.")

        self.checkbox_grayscale = self.create_checkbox("Grayscale", self.preprocess_tab, 'checkbox_grayscale', (250, 10, 201, 20))

        self.checkbox_remove_noise = self.create_checkbox("Remove noise", self.preprocess_tab, 'checkbox_remove_noise', (160, 45, 180, 20))

        # Smoothing
        smoothing_outer_widget = QWidget(self.preprocess_tab)
        smoothing_outer_widget.setGeometry(0, 70, 409, 71)
        smoothing_layout = QHBoxLayout(smoothing_outer_widget)
        smoothing_groupbox = QGroupBox("Smoothing")

        self.combobox_smoothing = QComboBox(smoothing_groupbox)
        self.combobox_smoothing.setObjectName('combobox_smoothing')
        self.combobox_smoothing.setGeometry(QRect(16, 22, 75, 22))
        self.smoothing_tooltip = {
            'Average': "Average Blurring",
            'Gaussian': "Gaussian Blurring",
            'Median': "Median Blurring",
            'Bilateral': "Bilateral Blurring"
        }
        for cb_text, tooltip in self.smoothing_tooltip.items():
            self.combobox_smoothing.addItem(str(cb_text))
        try:
            img_sm_value = int(self.config['preprocess']['smoothing'])
            valid_oem_value = max(0, min(img_sm_value, 3))
            self.combobox_smoothing.setCurrentIndex(valid_oem_value)
        except ValueError as e:
            logger.error(f"Error converting oem value to integer: {e}")
        self.combobox_smoothing.currentIndexChanged.connect(lambda: (self.update_combobox_smoothing(), self.toggle_apply_button()))

        self.label_smoothing_kernel = self.create_label("K:", smoothing_groupbox, 'label_smoothing_kernel', (100, 25, 10, 16))
        self.label_bilateral_diameter = self.create_label("D:", smoothing_groupbox, 'label_bilateral_diameter', (100, 25, 10, 16))
        self.label_bilateral_sigmacolor = self.create_label("SC:", smoothing_groupbox, 'label_bilateral_sigmacolor', (170, 25, 20, 16))
        self.label_bilateral_sigmaspace = self.create_label("SS:", smoothing_groupbox, 'label_bilateral_sigmaspace', (246, 25, 20, 16))

        self.spinbox_average_kernel = self.create_spinbox(smoothing_groupbox, 'spinbox_average_kernel', (117, 23, 40, 20), 1, 10, 1)
        self.spinbox_gaussian_kernel = self.create_spinbox(smoothing_groupbox, 'spinbox_gaussian_kernel', (117, 23, 40, 20), 1, 15, 2)
        self.spinbox_median_kernel = self.create_spinbox(smoothing_groupbox, 'spinbox_median_kernel', (117, 23, 40, 20), 1, 15, 2)
        self.spinbox_bilateral_diameter = self.create_spinbox(smoothing_groupbox, 'spinbox_bilateral_diameter', (117, 23, 40, 20), 1, 10, 1)
        self.spinbox_bilateral_sigmacolor = self.create_spinbox(smoothing_groupbox, 'spinbox_bilateral_sigmacolor', (193, 23, 40, 20), 1, 99, 1)
        self.spinbox_bilateral_sigmaspace = self.create_spinbox(smoothing_groupbox, 'spinbox_bilateral_sigmaspace', (267, 23, 40, 20), 1, 99, 1)

        smoothing_layout.addWidget(smoothing_groupbox)

        # Thresholding
        thresholding_outer_widget = QWidget(self.preprocess_tab)
        thresholding_outer_widget.setGeometry(0, 130, 409, 71)
        thresholding_layout = QHBoxLayout(thresholding_outer_widget)
        thresholding_groupbox = QGroupBox("Thresholding")

        self.checkbox_adaptive_thresholding = self.create_checkbox("Adaptive:", thresholding_groupbox,
                                                                   'checkbox_adaptive_thresholding', (20, 21, 180, 20))

        self.spinbox_adaptive_threshold = self.create_spinbox(thresholding_groupbox, 'spinbox_adaptive_threshold', (98, 21, 45, 20), 1, 255, 2)

        self.checkbox_global_thresholding = self.create_checkbox("Global:", thresholding_groupbox, 'checkbox_global_thresholding', (185, 21, 180, 20),
                                                                 tooltip="Enable this option to convert the image to a binary format.\n"
                                                                         "Binarization simplifies the image by separating pixels into black\n"
                                                                         "and white, making it suitable for various image processing tasks.")

        self.spinbox_global_threshold = self.create_spinbox(thresholding_groupbox, 'spinbox_global_threshold', (250, 21, 45, 20), 1, 255, 1,
                                                            tooltip="Threshold minimum = 0, maximum = 255\n"
                                                                    "Set the threshold value for binarization. Pixels with values above\n"
                                                                    "this threshold will be set to white, and those below will be black.\n"
                                                                    "Adjust the threshold based on the characteristics of your image.")

        thresholding_layout.addWidget(thresholding_groupbox)

        # Structure Manipulation
        struct_m_outer_widget = QWidget(self.preprocess_tab)
        struct_m_outer_widget.setGeometry(0, 190, 409, 71)
        struct_m_layout = QHBoxLayout(struct_m_outer_widget)
        struct_m_groupbox = QGroupBox("Structure Manipulation")

        self.checkbox_dilate = self.create_checkbox("Dilate", struct_m_groupbox, 'checkbox_dilate', (20, 21, 180, 20))
        self.checkbox_erode = self.create_checkbox("Erode", struct_m_groupbox, 'checkbox_erode', (90, 21, 180, 20))

        self.label_struct_m_kernel = self.create_label("K:", struct_m_groupbox, 'label_struct_m_kernel', (150, 23, 121, 16))
        self.label_struct_m_iteration = self.create_label("I:", struct_m_groupbox, 'label_struct_m_iteration', (220, 23, 121, 16))

        self.spinbox_struct_m_kernel = self.create_spinbox(struct_m_groupbox, 'spinbox_struct_m_kernel', (165, 21, 40, 20), 1, 10, 1)
        self.spinbox_struct_m_iteration = self.create_spinbox(struct_m_groupbox, 'spinbox_struct_m_iteration', (235, 21, 40, 20), 1, 10, 1)

        struct_m_layout.addWidget(struct_m_groupbox)

        # ======== OUTPUT TAB ========

        self.output_tab = QWidget()
        self.output_tab.setObjectName('output_tab')
        self.settings_tab_widget.addTab(self.output_tab, "Output")

        self.checkbox_copy_to_clipboard = self.create_checkbox("Copy to clipboard", self.output_tab, 'checkbox_copy_to_clipboard',
                                                               (16, 10, 141, 20))

        self.checkbox_show_popup_window = self.create_checkbox("Show popup window (OCR Text)", self.output_tab, 'checkbox_show_popup_window',
                                                               (16, 40, 190, 20))

        self.checkbox_remove_empty_lines = self.create_checkbox("Remove empty lines in OCR text", self.output_tab, 'checkbox_remove_empty_lines',
                                                                (16, 70, 190, 20))

        self.checkbox_save_captured_image = self.create_checkbox("Save captured image", self.output_tab, 'checkbox_save_captured_image',
                                                                 (16, 100, 171, 20))

        self.checkbox_save_enhanced_image = self.create_checkbox("Save enhanced image", self.output_tab, 'checkbox_save_enhanced_image',
                                                                 (16, 130, 171, 20))

        self.label_output_folder = self.create_label("Output folder:", self.output_tab, 'label_output_folder', (15, 163, 81, 16))

        self.line_edit_output_folder = self.create_line_edit(self.output_tab, 'line_edit_output_folder', (95, 161, 251, 22), lambda: 0)

        self.button_output_folder = self.create_button(". . .", self.output_tab, 'button_output_folder', (350, 160, 24, 24), False,
                                                       self.select_autosave_output_folder)

        # ======== TRANSLATE TAB ========

        self.translate_tab = QWidget()
        self.translate_tab.setObjectName('translate_tab')
        self.settings_tab_widget.addTab(self.translate_tab, "Translate")

        self.checkbox_append_translation = self.create_checkbox("Append translation to clipboard", self.translate_tab,
                                                                'checkbox_append_translation', (16, 10, 201, 20))

        self.checkbox_show_translation = self.create_checkbox("Show translation in popup window", self.translate_tab,
                                                              'checkbox_show_translation', (16, 40, 211, 20))

        # TABLE WIDGET - Translate To
        self.translate_table_widget = QTableWidget(self.translate_tab)
        table_header_labels = ["OCR Language", "Translate To (Using Google Translate)"]

        header_horizontal = MyHeader(Qt.Horizontal, self.translate_table_widget)
        self.translate_table_widget.setHorizontalHeader(header_horizontal)

        header_vertical = MyHeader(Qt.Vertical, self.translate_table_widget)
        self.translate_table_widget.setVerticalHeader(header_vertical)

        self.translate_table_widget.setColumnCount(2)
        self.translate_table_widget.setRowCount(110)
        self.translate_table_widget.setHorizontalHeaderLabels(table_header_labels)
        self.translate_table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Make the entire table read-only
        self.translate_table_widget.setSelectionMode(QAbstractItemView.NoSelection)  # No items can be selected

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

            self.translate_table_widget.setItem(table_row, 0, table_widget_language)
            self.translate_table_widget.setCellWidget(table_row, 1, translate_to_combobox)
            self.translate_to_comboboxes.append(translate_to_combobox)
            translate_to_combobox.currentIndexChanged.connect(self.toggle_apply_button)

        # Make 'Translate To' column stretch to fill table width.
        header_horizontal.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_horizontal.setSectionResizeMode(1, QHeaderView.Stretch)

        self.translate_table_widget.setObjectName('translate_table_widget')
        self.translate_table_widget.setGeometry(QRect(5, 70, 399, 189))
        self.translate_table_widget.verticalHeader().setVisible(False)
        self.settings_tab_widget.currentChanged.connect(self.handle_tab_change)

        # Define widgets related to OCR language and scroll area, which are used in the 'ocr_button_clicked_toggle_widgets_display' function.
        # 'ocr_tab_widgets' contains all child widgets of 'ocr_tab' excluding those in 'ocr_tab_language_widgets' and 'scroll_area_widgets'.
        ocr_tab_language_widgets = [self.label_ocr_language, self.button_ocr_language]
        ocr_tab_scroll_area_widgets = self.scroll_area.findChildren(QWidget)
        self.ocr_tab_widgets = set(self.ocr_tab.findChildren(QWidget)) - set(ocr_tab_language_widgets + ocr_tab_scroll_area_widgets)

    @staticmethod
    def create_label(text, parent, object_name, geometry):
        label = QLabel(text, parent)
        label.setObjectName(object_name)
        label.setGeometry(QRect(*geometry))
        return label

    @staticmethod
    def create_button(text, parent, object_name, geometry, auto_default, clicked_slot):
        button = QPushButton(text, parent)
        button.setObjectName(object_name)
        button.setGeometry(QRect(*geometry))
        button.setAutoDefault(auto_default)
        button.clicked.connect(clicked_slot)
        return button

    def create_checkbox(self, text, parent, object_name, geometry, clicked_slot=None, tooltip=None):
        checkbox = QCheckBox(text, parent)
        checkbox.setObjectName(object_name)
        checkbox.setGeometry(QRect(*geometry))
        if tooltip:
            checkbox.setToolTip(tooltip)
        checkbox.stateChanged.connect(self.toggle_apply_button)
        if clicked_slot:
            checkbox.clicked.connect(clicked_slot)
        return checkbox

    def create_spinbox(self, parent, object_name, geometry, minimum, maximum, step, tooltip=None):
        spinbox = QSpinBox(parent)
        spinbox.setObjectName(object_name)
        spinbox.setGeometry(QRect(*geometry))
        spinbox.setMinimum(minimum)
        spinbox.setMaximum(maximum)
        spinbox.setSingleStep(step)
        if tooltip:
            spinbox.setToolTip(tooltip)
        spinbox.valueChanged.connect(lambda value, name=object_name: (self.disable_spinbox_highlight(value, name),
                                                                      self.toggle_apply_button()))
        spinbox.editingFinished.connect(self.toggle_apply_button)
        spinbox.lineEdit().installEventFilter(self)
        self.spinboxes[object_name] = spinbox
        return spinbox

    def create_line_edit(self, parent, object_name, geometry, editing_finished_slot):
        line_edit = QLineEdit(parent)
        line_edit.setObjectName(object_name)
        line_edit.setGeometry(QRect(*geometry))
        line_edit.setCursorPosition(0)
        line_edit.textChanged.connect(self.toggle_apply_button)
        if editing_finished_slot:
            line_edit.editingFinished.connect(editing_finished_slot)
        line_edit.installEventFilter(self)
        self.line_edits[object_name] = line_edit
        return line_edit

    def initialize_settings_components(self):
        logger.info("Initializing settings component")
        self.config = load_config()
        self.initialize_settings_components_finish = False

        widgets = [
            (self.checkbox_minimize_to_sys_tray, 'preferences', 'minimize_to_system_tray'),
            (self.checkbox_play_sound, 'preferences', 'enable_sound'),
            (self.line_edit_sound_file, 'preferences', 'sound_file', True),
            (self.checkbox_pres_iw_spc, 'ocr', 'preserve_interword_spaces'),
            (self.line_edit_blacklist_char, 'ocr', 'blacklist_char'),
            (self.line_edit_whitelist_char, 'ocr', 'whitelist_char'),
            (self.checkbox_blacklist_char, 'ocr', 'enable_blacklist_char'),
            (self.checkbox_whitelist_char, 'ocr', 'enable_whitelist_char'),
            (self.line_edit_tesseract_path, 'ocr', 'tesseract_path'),
            (self.spinbox_scale_factor, 'preprocess', 'scale_factor'),
            (self.checkbox_enable_preprocess, 'preprocess', 'enable_preprocess'),
            (self.checkbox_grayscale, 'preprocess', 'grayscale'),
            (self.combobox_smoothing, 'preprocess', 'smoothing'),
            (self.spinbox_average_kernel, 'preprocess', 'average_blur_kernel'),
            (self.spinbox_gaussian_kernel, 'preprocess', 'gaussian_blur_kernel'),
            (self.spinbox_median_kernel, 'preprocess', 'median_blur_kernel'),
            (self.spinbox_bilateral_diameter, 'preprocess', 'bilateral_blur_diameter'),
            (self.spinbox_bilateral_sigmacolor, 'preprocess', 'bilateral_blur_sigmacolor'),
            (self.spinbox_bilateral_sigmaspace, 'preprocess', 'bilateral_blur_sigmaspace'),
            (self.checkbox_remove_noise, 'preprocess', 'remove_noise'),
            (self.checkbox_adaptive_thresholding, 'preprocess', 'adaptive_thresholding'),
            (self.spinbox_adaptive_threshold, 'preprocess', 'adaptive_threshold'),
            (self.checkbox_global_thresholding, 'preprocess', 'global_thresholding'),
            (self.spinbox_global_threshold, 'preprocess', 'global_threshold'),
            (self.checkbox_dilate, 'preprocess', 'dilate'),
            (self.checkbox_erode, 'preprocess', 'erode'),
            (self.spinbox_struct_m_kernel, 'preprocess', 'structure_manipulation_kernel'),
            (self.spinbox_struct_m_iteration, 'preprocess', 'structure_manipulation_iteration'),
            (self.checkbox_deskew, 'preprocess', 'deskew'),
            (self.checkbox_copy_to_clipboard, 'output', 'copy_to_clipboard'),
            (self.checkbox_show_popup_window, 'output', 'show_popup_window'),
            (self.checkbox_remove_empty_lines, 'output', 'remove_empty_lines'),
            (self.checkbox_save_captured_image, 'output', 'save_captured_image'),
            (self.checkbox_save_enhanced_image, 'output', 'save_enhanced_image'),
            (self.line_edit_output_folder, 'output', 'output_folder_path', True),
            (self.checkbox_show_translation, 'translate', 'enable_translation')
        ]

        for widget in widgets:
            self.init_widget(*widget)

        self.open_file_dialog_path = self.config['preferences']['sound_file']
        self.open_folder_dialog_path = self.config['output']['output_folder_path']
        self.update_combobox_psm_tooltip()
        self.update_combobox_oem_tooltip()
        self.update_combobox_smoothing()
        self.check_trained_data_language_file()

        if tesseract_check(self.config['ocr']['tesseract_path']):
            self.label_tesseract_version.setText(f"Tesseract Version: {tesseract_version()}")

        self.initialize_settings_components_finish = True

    def init_widget(self, widget, table_name, key, fix_line_edit=False):
        value = self.config[table_name][key]
        try:
            if isinstance(widget, QLineEdit):
                widget.setText(value if fix_line_edit else re.sub(r'\\+', r'\\', str(value).replace('/', '\\')))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(value)
        except (TypeError, ValueError, AttributeError):
            logger.error(f"Invalid configuration - Table: {table_name} | Key: {key} | Value: {value}")

    # valueChanged signal sends two argument (value, name)
    def disable_spinbox_highlight(self, value, name):
        self.spinboxes[name].lineEdit().setStyleSheet("""QLineEdit {
                                                 selection-background-color: white;
                                                 selection-color: black
                                                 }""")
        self.spinboxes[name].lineEdit().setReadOnly(True)

    def eventFilter(self, obj, event):
        # Clear the stylesheet when a mouse button is pressed inside the QLineEdit of any spin box
        for spinbox in self.spinboxes.values():
            if obj == spinbox.lineEdit() and event.type() == QEvent.MouseButtonPress:
                spinbox.lineEdit().setStyleSheet("")
                spinbox.setReadOnly(False)

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

    def update_combobox_psm_tooltip(self):
        tooltip = self.psm_tooltip.get(int(self.combobox_page_seg_mode.currentText()))
        self.combobox_page_seg_mode.setToolTip(tooltip)

    def update_combobox_oem_tooltip(self):
        tooltip = self.oem_tooltip.get(int(self.combobox_ocr_engine_mode.currentText()))
        self.combobox_ocr_engine_mode.setToolTip(tooltip)

    def update_combobox_smoothing(self):
        index = self.combobox_smoothing.currentIndex()

        self.label_smoothing_kernel.setVisible(index == 0 or index == 1 or index == 2)
        self.spinbox_average_kernel.setVisible(index == 0)
        self.spinbox_gaussian_kernel.setVisible(index == 1)
        self.spinbox_median_kernel.setVisible(index == 2)

        is_index_three = index == 3
        visibility = [self.label_bilateral_diameter,
                      self.label_bilateral_sigmacolor,
                      self.label_bilateral_sigmaspace,
                      self.spinbox_bilateral_diameter,
                      self.spinbox_bilateral_sigmaspace,
                      self.spinbox_bilateral_sigmacolor]

        for vis in visibility:
            vis.setVisible(is_index_three)

        tooltip = list(self.smoothing_tooltip.values())[index]
        self.combobox_smoothing.setToolTip(tooltip)

    def handle_tab_change(self):
        for spinbox in self.spinboxes.values():
            spinbox.clearFocus()

    def ocr_button_clicked_toggle_widgets_display(self):
        [widget.setVisible(False if not self.ocr_tab_widget_visible else True) for widget in self.ocr_tab_widgets]
        self.button_ocr_language.setText("Hide" if self.ocr_tab_widget_visible else "Show")
        self.scroll_area.setVisible(not self.ocr_tab_widget_visible)
        self.check_trained_data_language_file()
        self.ocr_tab_widget_visible = not self.ocr_tab_widget_visible

    def check_trained_data_language_file(self):
        logger.info("Checking trained data languages")
        self.config = load_config()
        for language_code, language_name in language_set().items():
            file_path = Path('./tessdata') / f'{language_code}.traineddata'
            is_file_exist = file_path.exists()
            is_language_selected = language_code in self.config['ocr']['language']

            self.sc_checkbox_dict[f'{language_name}'].setChecked(is_file_exist and is_language_selected)
            self.sc_checkbox_dict[f'{language_name}'].setEnabled(is_file_exist)
            self.sc_button_dict[f'{language_name}'].setVisible(not is_file_exist)

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

    def select_tesseract_executable_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Tesseract Executable", self.open_executable_dialog_path,
                                                   "Tesseract (tesseract.exe)", options=options)
        if file_path:
            formatted_file_path = file_path.replace('/', '\\')
            self.line_edit_tesseract_path.setText(formatted_file_path)
            self.open_executable_dialog_path = formatted_file_path
            if tesseract_check(formatted_file_path):
                self.label_tesseract_version.setText(f"Tesseract Version: {tesseract_version()}")

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
        if not self.apply_button_was_enabled:
            self.apply_button_state_timer.start()
            self.button_apply_settings.setEnabled(True)
            logger.info(f"Apply button color timer start - state: {self.apply_button_was_enabled}")

    def update_apply_button(self):
        self.apply_button_was_enabled = True
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
            logger.info(f"Apply button color timer stop - state: {self.apply_button_was_enabled}")
            self.apply_button_state_timer.stop()

    def stop_updating_apply_button(self):
        if self.apply_button_was_enabled:
            self.apply_button_state_timer.stop()  # Forcefully stop the update_apply_button
            palette = QPalette()
            palette.setColor(QPalette.ButtonText, QColor(128, 128, 128))  # Gray color
            self.button_apply_settings.setPalette(palette)
            self.button_apply_settings.setEnabled(False)
            self.apply_button_was_enabled = False
            logger.info(f"Apply button state: {self.apply_button_was_enabled}")

    def apply_button_clicked(self):
        try:
            self.button_OK_settings.setDefault(False)
            self.check_sound_file()
            self.check_and_create_output_folder()
            self.check_trained_data_language_file()
            self.button_OK_settings.setFocus()
            if self.output_folder_created:
                self.stop_updating_apply_button()
        except ValueError as e:
            show_message_box("Critical", "Error", str(e))

    def ok_button_clicked(self):
        try:
            self.finished.emit(0)  # For on_settings_ui_closed method in MainUI, for disabling 'Settings' menu in system tray
            self.check_sound_file()
            self.check_and_create_output_folder()
            if self.output_folder_created:
                self.stop_updating_apply_button()
                self.hide()
        except ValueError as e:
            show_message_box("Critical", "Error", str(e))

    def cancel_button_clicked(self):
        self.close()

    def check_sound_file(self):
        if self.checkbox_play_sound.isChecked():
            if not self.line_edit_sound_file.text():
                raise ValueError("Sound file is empty.")
            if not Path(self.line_edit_sound_file.text()).exists():
                raise ValueError(f"Sound file does not exist.")

    def check_and_create_output_folder(self):
        output_folder_path = self.fix_line_edit_path(self.line_edit_output_folder)
        self.line_edit_output_folder.setText(output_folder_path)

        if not output_folder_path:
            if self.checkbox_save_captured_image.isChecked() or self.checkbox_save_enhanced_image.isChecked():
                self.settings_tab_widget.setCurrentIndex(3)
                raise ValueError("Output folder is empty.")

        if Path(output_folder_path).exists() and Path(output_folder_path).is_dir():
            logger.info(f"Output folder found '{output_folder_path}'")
            self.output_folder_created = True
            self.save_settings_config()
            return

        self.settings_tab_widget.setCurrentIndex(3)
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

    def save_settings_window_position(self):
        window_position_x = self.pos().x()
        window_position_y = self.pos().y()
        self_pos_xy = {"miscellaneous": {'settings_window_position_x': window_position_x, 'settings_window_position_y': window_position_y}}
        logger.info(f"Settings window saved position: X: {window_position_x} Y: {window_position_y}")
        update_config(self_pos_xy)

    def load_settings_window_position(self):
        self.config = load_config()
        pos_x = self.config['miscellaneous']['settings_window_position_x']
        pos_y = self.config['miscellaneous']['settings_window_position_y']
        self.move(pos_x, pos_y)

    def download_from_github(self):
        sender_button = self.sender()

        for name, button in self.sc_button_dict.items():
            if button is sender_button:
                for language_code, language_name in language_set().items():
                    if name == language_name:
                        tessdata_folder = Path('./tessdata/')
                        file_name = f'{language_code}.traineddata'
                        download_destination = f'{tessdata_folder}/{file_name}.tmp'
                        tessdata_folder.mkdir(parents=True, exist_ok=True)

                        logger.info(f"Selected language: {language_name}")
                        self.download_trained_data.start_download_worker(language_name, download_destination, file_name)
                        break

    def toggle_download_button_progress_bar(self, language_name, is_visible):
        logger.info(f"Download button: {not is_visible} - Progress bar: {is_visible}")
        self.sc_button_dict[f'{language_name}'].setVisible(not is_visible)
        self.sc_progressbar_dict[f'{language_name}'].setVisible(is_visible)
        self.button_ocr_language.setEnabled(not is_visible)

    def update_progress_bar(self, language_name, value):
        self.sc_progressbar_dict[f'{language_name}'].setValue(value)
        if value == 100:
            self.sc_progressbar_dict[f'{language_name}'].setVisible(False)
            self.sc_checkbox_dict[f'{language_name}'].setEnabled(True)
            self.button_ocr_language.setEnabled(True)
            self.scroll_area.update()

    def save_settings_config(self):
        settings_config = {
            "preferences": {
                'minimize_to_system_tray': self.checkbox_minimize_to_sys_tray.isChecked(),
                'enable_sound': self.checkbox_play_sound.isChecked(),
                'sound_file': self.fix_line_edit_path(self.line_edit_sound_file)
            },
            "ocr": {
                'tesseract_path': self.line_edit_tesseract_path.text(),
                'page_segmentation_mode': int(self.combobox_page_seg_mode.currentText()),
                'ocr_engine_mode': int(self.combobox_ocr_engine_mode.currentText()),
                'preserve_interword_spaces': self.checkbox_pres_iw_spc.isChecked(),
                'enable_blacklist_char': self.checkbox_blacklist_char.isChecked(),
                'blacklist_char': self.line_edit_blacklist_char.text(),
                'enable_whitelist_char': self.checkbox_whitelist_char.isChecked(),
                'whitelist_char': self.line_edit_whitelist_char.text()
            },
            "preprocess": {
                'enable_preprocess': self.checkbox_enable_preprocess.isChecked(),
                'scale_factor': self.fix_double_spinbox_zeros(self.spinbox_scale_factor.value()),
                'grayscale': self.checkbox_grayscale.isChecked(),
                'smoothing': self.combobox_smoothing.currentIndex(),
                'average_blur_kernel': self.spinbox_average_kernel.value(),
                'gaussian_blur_kernel': self.spinbox_gaussian_kernel.value(),
                'median_blur_kernel': self.spinbox_median_kernel.value(),
                'bilateral_blur_diameter': self.spinbox_bilateral_diameter.value(),
                'bilateral_blur_sigmacolor': self.spinbox_bilateral_sigmacolor.value(),
                'bilateral_blur_sigmaspace': self.spinbox_bilateral_sigmaspace.value(),
                'remove_noise': self.checkbox_remove_noise.isChecked(),
                'adaptive_thresholding': self.checkbox_adaptive_thresholding.isChecked(),
                'adaptive_threshold': self.spinbox_adaptive_threshold.value(),
                'global_thresholding': self.checkbox_global_thresholding.isChecked(),
                'global_threshold': self.spinbox_global_threshold.value(),
                'dilate': self.checkbox_dilate.isChecked(),
                'erode': self.checkbox_erode.isChecked(),
                'structure_manipulation_kernel': self.spinbox_struct_m_kernel.value(),
                'structure_manipulation_iteration': self.spinbox_struct_m_iteration.value(),
                'deskew': self.checkbox_deskew.isChecked()
            },
            "output": {
                'copy_to_clipboard': self.checkbox_copy_to_clipboard.isChecked(),
                'show_popup_window': self.checkbox_show_popup_window.isChecked(),
                'remove_empty_lines': self.checkbox_remove_empty_lines.isChecked(),
                'save_captured_image': self.checkbox_save_captured_image.isChecked(),
                'save_enhanced_image': self.checkbox_save_enhanced_image.isChecked(),
                'output_folder_path': self.fix_line_edit_path(self.line_edit_output_folder)
            },
            "translate": {
                'enable_translation': self.checkbox_show_translation.isChecked()
            }
        }
        # Save all checked OCR languages to config
        checked_languages = [
            language_code for language_code, language_name in language_set().items()
            if self.sc_checkbox_dict[language_name].isChecked() and Path('./tessdata', f'{language_code}.traineddata').exists()
        ]
        settings_config['ocr']['language'] = '+'.join(checked_languages)

        # Get the selected language in every Translate To combobox
        languages = language_list()
        for count, language_name in enumerate(languages.values()):
            current_text = self.translate_to_comboboxes[count].currentText().lower()
            for language_code, name in languages.items():
                if name == current_text:
                    settings_config['translate'][language_name] = language_code

        logger.info("Saving settings in configuration file")
        update_config(settings_config)

    @staticmethod
    def fix_line_edit_path(line_edit: QLineEdit):
        return re.sub(r'\\+', r'\\', str(line_edit.text()).replace('/', '\\'))

    @staticmethod
    def fix_double_spinbox_zeros(value):
        return float(format(value, '.7f').rstrip('0').rstrip('.'))

    def closeEvent(self, event):
        self.stop_updating_apply_button()
        self.finished.emit(0)  # For on_settings_ui_closed method in MainUI, for disabling 'Settings' menu in system tray
        self.close()
        logger.info("Settings window closed")


# For Translate Table Widget
class MyHeader(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def paintSection(self, painter: QPainter, rect: QRect, index: int) -> None:
        painter.setFont(self.font())
        super().paintSection(painter, rect, index)
