# Standard libraries
import re
from pathlib import Path

# Third-party libraries
from loguru import logger
from PySide6.QtCore import Qt, QRect, QTimer, QEvent
from PySide6.QtGui import QColor, QPalette, QIcon, QPainter
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog, QDoubleSpinBox,
                               QFileDialog, QHeaderView, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QProgressBar, QScrollArea, QSpinBox, QTableWidget, QTableWidgetItem,
                               QTabWidget, QVBoxLayout, QWidget)

# Custom libraries
from src.config.config import load_config, update_config
from src.ocr.ocr_processor import tesseract_check, tesseract_version
from src.ui.asset_manager import app_icon
from src.utils.message_box import show_message_box
from src.utils.translate import googletrans_languages, tesseract_languages, tesseract_skip_languages
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
        for language_name in tesseract_languages().values():
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
            3: "Fully automatic page segmentation,\nbut no OSD. (Default)",
            4: "Assume a single column\nof text of variable sizes. ",
            5: "Assume a single uniform block\nof vertically aligned text. ",
            6: "Assume a single uniform block of text. ",
            7: "Treat the image as a single text line. ",
            8: "Treat the image as a single word. ",
            9: "Treat the image as a single word in a circle. ",
            10: "Treat the image as a single character. ",
            11: "Sparse text. Find as much text as\npossible in no particular order. ",
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
                                                         tooltip="Enable this option to preserve interword\n"
                                                                 "spaces in the OCR output. This helps\n"
                                                                 "maintain the original spacing between\n"
                                                                 "words in the recognized text.")
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

        self.checkbox_enable_preprocess = self.create_checkbox("Enable Preprocess", self.preprocess_tab, 'checkbox_enable_preprocess',
                                                               (16, 10, 201, 20))

        # Scale Factor
        self.label_scale_factor = self.create_label("Scale Factor:", self.preprocess_tab, 'label_scale_factor', (22, 47, 121, 16),
                                                    tooltip="Modifies image size based on the scale factor.\n"
                                                            "Use 1.0 for original size, and values over 1.0\n"
                                                            "to enlarge. For instance, 1.5 increases size by\n"
                                                            "50%, 2.0 doubles it.")
        self.spinbox_scale_factor = QDoubleSpinBox(self.preprocess_tab)
        self.spinbox_scale_factor.setObjectName('spinbox_scale_factor')
        self.spinbox_scale_factor.setGeometry(QRect(96, 46, 30, 19))
        self.spinbox_scale_factor.setMinimum(1.0)
        self.spinbox_scale_factor.setMaximum(10.0)
        self.spinbox_scale_factor.setSingleStep(0.1)
        self.spinbox_scale_factor.setDecimals(1)
        self.spinbox_scale_factor.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.spinbox_scale_factor.valueChanged.connect(lambda value, name='spinbox_scale_factor':
                                                       (self.disable_spinbox_highlight(value, name),
                                                        self.toggle_apply_button()))
        self.spinbox_scale_factor.editingFinished.connect(self.toggle_apply_button)
        self.spinbox_scale_factor.lineEdit().installEventFilter(self)
        self.spinboxes['spinbox_scale_factor'] = self.spinbox_scale_factor  # Add to the dictionary

        self.checkbox_grayscale = self.create_checkbox("Grayscale", self.preprocess_tab, 'checkbox_grayscale', (160, 45, 69, 20),
                                                       tooltip="Enables grayscale conversion. This\n"
                                                               "transforms the image into shades of\n"
                                                               "gray, enhancing contrast and detail\n"
                                                               "for further image processing tasks.")
        self.checkbox_remove_noise = self.create_checkbox("Remove noise", self.preprocess_tab, 'checkbox_remove_noise', (250, 45, 93, 20),
                                                          tooltip="Enables noise removal process. This\n"
                                                                  "uses global thresholding and connected\n"
                                                                  "components with statistics to identify\n"
                                                                  "and filter out small dotted regions based\n"
                                                                  "on size.")

        # Deskew
        self.label_deskew = self.create_label("Deskew:", self.preprocess_tab, 'label_deskew', (45, 80, 70, 16),
                                              tooltip="Enable this option to automatically straighten\n"
                                                      "skewed text in the image. Improved alignment\n"
                                                      "enhances OCR accuracy, making text extraction\n"
                                                      "more efficient. Ideal for scanned document or\n"
                                                      "image with tilted text.")
        self.checkbox_deskew = self.create_checkbox("", self.preprocess_tab, 'checkbox_deskew', (95, 79, 180, 20))
        self.tooltip_deskew = {'First': "Deskew the image before preprocessing",
                               'Last': "Deskew the image after preprocessing"}
        self.combobox_deskew = self.create_combobox((115, 77, 75, 22), self.tooltip_deskew, 'combobox_deskew', 'preprocess',
                                                    'blurring', 1, self.update_combobox_deskew)

        # Blur
        # Diameter, SigmaColor and SigmaSpace is used by Bilateral Blurring
        self.label_blur = self.create_label("Blurring:", self.preprocess_tab, 'label_blur', (43, 115, 70, 16),
                                            tooltip="Applies a blur effect to the image. This helps\n"
                                                    "reduce high-frequency noise and detail in the\n"
                                                    "image, making it easier to identify key features\n"
                                                    "and patterns.")
        self.checkbox_blur = self.create_checkbox("", self.preprocess_tab, "checkbox_blur", (95, 116, 15, 15))
        self.tooltip_blur = {'Average': "Average Blur works by averaging the pixel values in\n"
                                        "the neighborhood defined by the kernel, resulting in\n"
                                        "a smoothing effect. It's a straightforward method but\n"
                                        "might not preserve edges well.",
                             'Gaussian': "Gaussian Blur uses a Gaussian kernel, giving more\n"
                                         "weight to the nearby pixels and less to the distant\n"
                                         "ones. This method provides a more natural blurring\n"
                                         "effect and preserves edges better than Box Blur.",
                             'Median': "Median Blur replaces each pixel's value with the median\n"
                                       "of the pixel values in its neighborhood. It's particularly\n"
                                       "effective at reducing salt-and-pepper noise.",
                             'Bilateral': "Bilateral Blurring" "Bilateral Blur is a more advanced\n"
                                          "method that also takes into account the intensity\n"
                                          "difference between pixels. It can preserve edges\n"
                                          "while still reducing noise."}
        self.combobox_blur = self.create_combobox((115, 112, 75, 22), self.tooltip_blur, 'combobox_blur', 'preprocess',
                                                  'blurring', 3, self.update_combobox_blurring)
        self.label_blur_kernel = self.create_label("K:", self.preprocess_tab, 'label_blur_kernel', (200, 115, 10, 16), tooltip="Kernel")
        self.label_blur_diameter = self.create_label("D:", self.preprocess_tab, 'label_blur_diameter', (200, 115, 10, 16), tooltip="Diameter")
        self.label_blur_sigmacolor = self.create_label("C:", self.preprocess_tab, 'label_blur_sigmacolor', (250, 115, 20, 16), tooltip="Sigma Color")
        self.label_blur_sigmaspace = self.create_label("S:", self.preprocess_tab, 'label_blur_sigmaspace', (300, 115, 20, 16), tooltip="Sigma Space")
        self.spinbox_blur_kernel_h = self.create_spinbox(self.preprocess_tab, 'spinbox_average_kernel_h', (215, 113, 30, 19), 1, 15, 1)
        self.spinbox_blur_kernel_v = self.create_spinbox(self.preprocess_tab, 'spinbox_average_kernel_v', (250, 113, 30, 19), 1, 15, 1)
        self.spinbox_blur_diameter = self.create_spinbox(self.preprocess_tab, 'spinbox_blur_diameter', (215, 113, 30, 19), 1, 10, 1)
        self.spinbox_blur_sigmacolor = self.create_spinbox(self.preprocess_tab, 'spinbox_blur_sigmacolor', (265, 113, 30, 19), 1, 256, 1)
        self.spinbox_blur_sigmaspace = self.create_spinbox(self.preprocess_tab, 'spinbox_blur_sigmaspace', (315, 113, 30, 19), 1, 256, 1)

        # Thresholding
        self.label_thresholding = self.create_label("Thresholding:", self.preprocess_tab, 'label_thresholding', (16, 150, 75, 16),
                                                    tooltip="Converts the image into a binary\n"
                                                            "format by setting a threshold value.")
        self.checkbox_thresholding = self.create_checkbox("", self.preprocess_tab, "checkbox_thresholding", (95, 151, 15, 15))
        self.tooltip_thresholding = {'Global': "Global Thresholding applies a single, global threshold value\n"
                                               "to the entire image. All the pixel intensity values higher than\n"
                                               "this threshold are set to one value (typically white), while\n"
                                               "those lower are set to another value (typically black). It's\n"
                                               "simple and fast, but might not work well if the image has\n"
                                               "different lighting conditions in different areas.",
                                     'Adaptive': "Adaptive Thresholding applies different thresholds\n"
                                                 "for different regions of the image, which provides\n"
                                                 "better results for images with varying illumination.",
                                     'Otsu': "Otsu's Thresholding automatically determines\n"
                                             "the optimal threshold value based on the image's\n"
                                             "histogram."}
        self.combobox_thresholding = self.create_combobox((115, 147, 75, 22), self.tooltip_thresholding, 'combobox_thresholding', 'preprocess',
                                                          'thresholding', 1, self.update_combobox_thresholding)
        self.label_threshold = self.create_label("T:", self.preprocess_tab, 'label_threshold', (200, 150, 10, 16), tooltip="Threshold")
        self.label_global_type = self.create_label("T:", self.preprocess_tab, 'label_global_type', (250, 150, 15, 16), tooltip="Threshold Type")
        self.tooltip_global_type = {'Binary': "Transforms pixel values. Values exceeding\n"
                                              "the threshold become the maximum, or\n"
                                              "else become zero.",
                                    'Inverse': "Inverse of binary thresholding. Pixel values\n"
                                               "exceeding the threshold become zero,\n"
                                               "otherwise they become the maximum.",
                                    'Truncate': "Pixel values exceeding the threshold\n"
                                                "are truncated to the threshold. Values\n"
                                                "below the threshold remain unchanged.",
                                    'ToZero': "Pixel values exceeding the threshold\n"
                                              "remain the same, values below the\n"
                                              "threshold become zero.",
                                    'ZeroInv': "Inverse of to-zero thresholding. Pixel\n"
                                               "values exceeding the threshold become\n"
                                               "zero, values below the threshold remain\n"
                                               "unchanged."
                                    }
        self.combobox_global_type = self.create_combobox((268, 147, 75, 22), self.tooltip_global_type, 'combobox_global_type',
                                                         'preprocess', 'threshold_global_type', 1, self.update_combobox_thresh_global_type)
        self.label_adaptive_method = self.create_label("M:", self.preprocess_tab, 'label_adaptive_method', (250, 150, 15, 16), tooltip="Method")
        self.spinbox_threshold = self.create_spinbox(self.preprocess_tab, 'spinbox_threshold', (215, 148, 30, 19), 1, 255, 2)
        self.tooltip_adaptive_method = {'Mean': "Sets the threshold for a pixel based on\n"
                                                "the average of its surrounding pixels,\n"
                                                "minus a constant value.",
                                        'Gaussian': "Sets the threshold for a pixel based on\n"
                                                    "a weighted average of its surrounding\n"
                                                    "pixels, giving more importance to the\n"
                                                    "closer ones, minus a constant value."}
        self.combobox_adaptive_method = self.create_combobox((268, 147, 75, 22), self.tooltip_adaptive_method, 'combobox_adaptive_method',
                                                             'preprocess', 'threshold_adaptive_method', 1, self.update_combobox_adaptive_method)

        # Morphological Transformation
        self.label_morph = self.create_label("Morph Trans:", self.preprocess_tab, 'label_morph', (19, 185, 70, 16),
                                             tooltip="Morphological Transformation. Performs\n"
                                                     "operations based on the image's shape.\n"
                                                     "This can help remove noise, fill holes, or\n"
                                                     "identify structures within the image.")
        self.checkbox_morph = self.create_checkbox("", self.preprocess_tab, "checkbox_morph", (95, 186, 15, 15))
        self.tooltip_morph = {'Erosion': "Erosion shrinks the shapes in the image by\n"
                                         "peeling off pixels from their edges. Useful\n"
                                         "for removing small-scale noise and separating\n"
                                         "closely spaced elements.",
                              'Dilation': "Dilation expands the shapes in the image by\n"
                                          "adding pixels to their edges. Useful for filling\n"
                                          "small holes and connecting nearby elements.",
                              'Opening': "Opening is erosion followed by dilation.\n"
                                         "It helps to remove small-scale noise and\n"
                                         "to disconnect elements that are close\n"
                                         "together.",
                              'Closing': "Closing is dilation followed by erosion.\n"
                                         "It helps to fill small holes and gaps and\n"
                                         "to connect nearby elements.",
                              'Gradient': "Morphological Gradient shows the difference\n"
                                          "between dilation and erosion of an image,\n"
                                          "often resulting in an outline of the shapes\n"
                                          "in the image.",
                              'Top Hat': "Top Hat shows the difference between the\n"
                                         "original image and the result of applying\n"
                                         "the opening operation. It highlights bright\n"
                                         "spots in the image that are smaller than the\n"
                                         "structuring element.",
                              'Black Hat': "Black Hat shows the difference between\n"
                                           "the result of applying the closing operation\n"
                                           "and the original image. It highlights dark\n"
                                           "spots in the image that are smaller than the\n"
                                           "structuring element."}
        self.combobox_morph = self.create_combobox((115, 182, 75, 22), self.tooltip_morph, 'combobox_morph', 'preprocess',
                                                   'morphological_transformation', 6, self.update_combobox_morph)
        self.label_morph_kernel = self.create_label("K:", self.preprocess_tab, 'label_morph_kernel', (200, 185, 10, 16), tooltip="Kernel")
        self.label_morph_iteration = self.create_label("I:", self.preprocess_tab, 'label_morph_iteration', (285, 185, 10, 16), tooltip="Iteration")
        self.spinbox_morph_kernel_h = self.create_spinbox(self.preprocess_tab, 'spinbox_morph_kernel_h', (215, 183, 30, 19), 1, 15, 2)
        self.spinbox_morph_kernel_v = self.create_spinbox(self.preprocess_tab, 'spinbox_morph_kernel_v', (250, 183, 30, 19), 1, 15, 2)
        self.spinbox_morph_iteration = self.create_spinbox(self.preprocess_tab, 'spinbox_morph_iteration', (300, 183, 30, 19), 1, 10, 1)

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
        self.translate_table_widget.setRowCount(len(tesseract_languages()) - len(tesseract_skip_languages()))
        self.translate_table_widget.setHorizontalHeaderLabels(table_header_labels)
        self.translate_table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Make the entire table read-only
        self.translate_table_widget.setSelectionMode(QAbstractItemView.NoSelection)  # No items can be selected

        self.translate_to_comboboxes = []

        table_row = 0
        for combobox_language in tesseract_languages().values():
            if combobox_language in tesseract_skip_languages():
                continue
            table_widget_language = QTableWidgetItem(combobox_language.title())
            translate_to_combobox = QComboBox()

            for language_code, language_name in googletrans_languages().items():
                # Get the first word of the language_name and combobox_language
                first_word_language_name = language_name.split(' ')[0].lower()
                first_word_combobox_language = combobox_language.split(' ')[0].lower()
                # Add the languages with the first letter capitalized to the combo box, excluding the current language
                if first_word_language_name not in first_word_combobox_language:
                    translate_to_combobox.addItem(language_name.title())
                if language_code == self.config['translate']['languages'][table_row]:
                    index = translate_to_combobox.findText(language_name.capitalize())
                    if index >= 0:  # -1 means the text was not found
                        translate_to_combobox.setCurrentIndex(index)

            self.translate_table_widget.setItem(table_row, 0, table_widget_language)
            self.translate_table_widget.setCellWidget(table_row, 1, translate_to_combobox)
            self.translate_to_comboboxes.append(translate_to_combobox)
            translate_to_combobox.currentIndexChanged.connect(self.toggle_apply_button)
            table_row += 1

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
    def create_label(text, parent, object_name, geometry, tooltip=None):
        label = QLabel(text, parent)
        label.setObjectName(object_name)
        label.setGeometry(QRect(*geometry))
        label.setToolTip(tooltip)
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

    def create_combobox(self, geometry, tooltips, object_name, config_section, config_key, max_index, index_changed_callback):
        combobox = QComboBox(self.preprocess_tab)
        combobox.setObjectName(object_name)
        combobox.setGeometry(QRect(*geometry))
        for cb_text, tooltip in tooltips.items():
            combobox.addItem(str(cb_text))
        try:
            index = max(0, min(int(self.config[config_section][config_key]), max_index))
            combobox.setCurrentIndex(index)
        except ValueError as e:
            logger.error(f"Error converting value to integer: {e}")
        combobox.currentIndexChanged.connect(lambda: (index_changed_callback(), self.toggle_apply_button()))
        return combobox

    def create_spinbox(self, parent, object_name, geometry, minimum, maximum, step, tooltip=None):
        spinbox = QSpinBox(parent)
        spinbox.setObjectName(object_name)
        spinbox.setGeometry(QRect(*geometry))
        spinbox.setMinimum(minimum)
        spinbox.setMaximum(maximum)
        spinbox.setSingleStep(step)
        spinbox.setButtonSymbols(QSpinBox.NoButtons)
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
            (self.checkbox_grayscale, 'preprocess', 'enable_grayscale'),
            (self.checkbox_deskew, 'preprocess', 'enable_deskew'),
            (self.combobox_deskew, 'preprocess', 'deskew_position'),
            (self.checkbox_blur, 'preprocess', 'enable_blurring'),
            (self.combobox_blur, 'preprocess', 'blurring'),
            (self.checkbox_remove_noise, 'preprocess', 'remove_noise'),
            (self.checkbox_thresholding, 'preprocess', 'enable_thresholding'),
            (self.combobox_thresholding, 'preprocess', 'thresholding'),
            (self.combobox_global_type, 'preprocess', 'threshold_global_type'),
            (self.combobox_adaptive_method, 'preprocess', 'threshold_adaptive_method'),
            (self.checkbox_morph, 'preprocess', 'enable_morphological_transformation'),
            (self.combobox_morph, 'preprocess', 'morphological_transformation'),
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
        self.update_combobox_blurring()
        self.update_combobox_thresholding()
        self.update_combobox_thresh_global_type()
        self.update_combobox_adaptive_method()
        self.update_combobox_morph()
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
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(value)
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

    def update_combobox_deskew(self):
        index = self.combobox_deskew.currentIndex()
        tooltip = list(self.tooltip_deskew.values())[index]
        self.combobox_deskew.setToolTip(tooltip)

    def update_combobox_blurring(self):
        index = self.combobox_blur.currentIndex()
        tooltip = list(self.tooltip_blur.values())[index]
        self.combobox_blur.setToolTip(tooltip)
        settings_name = [
            'blur_average_kernel',
            'blur_gaussian_kernel',
            'blur_median_kernel',
        ]
        # Set visibility and values based on index.
        self.label_blur_kernel.setVisible(index != 3)
        self.spinbox_blur_kernel_h.setVisible(index != 3)
        self.spinbox_blur_kernel_v.setVisible(index != 2 and index != 3)

        if index == 0:
            self.spinbox_blur_kernel_h.setSingleStep(1)
            self.spinbox_blur_kernel_v.setSingleStep(1)
        else:
            self.spinbox_blur_kernel_h.setSingleStep(2)
            self.spinbox_blur_kernel_v.setSingleStep(2)

        if index < 2:
            self.spinbox_blur_kernel_h.setValue(self.config['preprocess'][settings_name[index]][0])
            self.spinbox_blur_kernel_v.setValue(self.config['preprocess'][settings_name[index]][1])
        elif index == 2:
            self.spinbox_blur_kernel_h.setValue(self.config['preprocess'][settings_name[index]])

        is_index_three = index == 3
        visibility = [self.label_blur_diameter,
                      self.label_blur_sigmacolor,
                      self.label_blur_sigmaspace,
                      self.spinbox_blur_diameter,
                      self.spinbox_blur_sigmaspace,
                      self.spinbox_blur_sigmacolor]

        for vis in visibility:
            vis.setVisible(is_index_three)

    def update_combobox_thresholding(self):
        index = self.combobox_thresholding.currentIndex()
        tooltip = list(self.tooltip_thresholding.values())[index]
        self.combobox_thresholding.setToolTip(tooltip)
        self.label_threshold.setVisible(index == 0 or index == 1)
        self.spinbox_threshold.setVisible(index == 0 or index == 1)
        self.label_global_type.setVisible(index == 0)
        self.combobox_global_type.setVisible(index == 0)
        self.label_adaptive_method.setVisible(index == 1)
        self.combobox_adaptive_method.setVisible(index == 1)

        if index == 0:
            self.spinbox_threshold.setValue(self.config['preprocess']['threshold_global'])
        if index == 1:
            self.spinbox_threshold.setValue(self.config['preprocess']['threshold_adaptive'])
            self.combobox_adaptive_method.setCurrentIndex(self.config['preprocess']['threshold_adaptive_method'])

    def update_combobox_thresh_global_type(self):
        index = self.combobox_global_type.currentIndex()
        tooltip = list(self.tooltip_global_type.values())[index]
        self.combobox_global_type.setToolTip(tooltip)

    def update_combobox_adaptive_method(self):
        index = self.combobox_adaptive_method.currentIndex()
        tooltip = list(self.tooltip_adaptive_method.values())[index]
        self.combobox_adaptive_method.setToolTip(tooltip)

    def update_combobox_morph(self):
        index = self.combobox_morph.currentIndex()
        self.label_morph_iteration.setVisible(index == 0 or index == 1)
        self.spinbox_morph_iteration.setVisible(index == 0 or index == 1)
        kernel_dict = {
            0: 'erosion_kernel_iteration',
            1: 'dilation_kernel_iteration',
            2: 'opening_kernel',
            3: 'closing_kernel',
            4: 'gradient_kernel',
            5: 'top_hat_kernel',
            6: 'black_hat_kernel'
        }
        if index in kernel_dict:
            kernel = kernel_dict[index]
            self.spinbox_morph_kernel_h.setValue(self.config['preprocess'][kernel][0])
            self.spinbox_morph_kernel_v.setValue(self.config['preprocess'][kernel][1])
            try:
                iteration = self.config['preprocess'][kernel][2]
                if iteration is not None:
                    self.spinbox_morph_iteration.setValue(iteration)
            except IndexError:
                pass

        tooltip = list(self.tooltip_morph.values())[index]
        self.combobox_morph.setToolTip(tooltip)

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
        for language_code, language_name in tesseract_languages().items():
            file_path = Path('./tessdata') / f'{language_code}.traineddata'
            is_file_exist = file_path.exists()
            is_language_selected = language_code in self.config['ocr']['language'].split('+')

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
                for language_code, language_name in tesseract_languages().items():
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
                'enable_grayscale': self.checkbox_grayscale.isChecked(),
                'remove_noise': self.checkbox_remove_noise.isChecked(),
                'enable_deskew': self.checkbox_deskew.isChecked(),
                'deskew_position': self.combobox_deskew.currentIndex(),
                'enable_blurring': self.checkbox_blur.isChecked(),
                'blurring': self.combobox_blur.currentIndex(),
                'enable_thresholding': self.checkbox_thresholding.isChecked(),
                'thresholding': self.combobox_thresholding.currentIndex(),
                'threshold_global_type': self.combobox_global_type.currentIndex(),
                'threshold_adaptive_method': self.combobox_adaptive_method.currentIndex(),
                'enable_morphological_transformation': self.checkbox_morph.isChecked(),
                'morphological_transformation': self.combobox_morph.currentIndex()
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
        # Save blurring kernel and other
        blur_index = self.combobox_blur.currentIndex()
        if blur_index == 0:
            settings_config['preprocess']['blur_average_kernel'] = [self.spinbox_blur_kernel_h.value(), self.spinbox_blur_kernel_v.value()]
        elif blur_index == 1:
            kvh = self.spinbox_morph_kernel_h.value()
            kvh = kvh if kvh % 2 else kvh + 1
            kvv = self.spinbox_morph_kernel_h.value()
            kvv = kvv if kvv % 2 else kvv + 1
            settings_config['preprocess']['blur_gaussian_kernel'] = [kvh, kvv]
        elif blur_index == 2:
            kvh = self.spinbox_blur_kernel_h.value()
            settings_config['preprocess']['blur_median_kernel'] = kvh if kvh % 2 else kvh + 1
        elif blur_index == 3:
            settings_config['preprocess']['blur_bilateral_dcs'] = [
                self.spinbox_blur_diameter.value(), self.spinbox_blur_sigmacolor.value(), self.spinbox_blur_sigmaspace.value()]

        # Save thresholding
        thresh_index = self.combobox_thresholding.currentIndex()
        settings_name = ['threshold_global', 'threshold_adaptive']
        if thresh_index in [0, 1]:
            settings_config['preprocess'][settings_name[thresh_index]] = self.spinbox_threshold.value()

        # Save morphological transformation
        morph_index = self.combobox_morph.currentIndex()
        settings_name = [
            'erosion_kernel_iteration',
            'dilation_kernel_iteration',
            'opening_kernel',
            'closing_kernel',
            'gradient_kernel',
            'top_hat_kernel',
            'black_hat_kernel'
        ]
        settings_values = {i: [self.spinbox_morph_kernel_h.value(), self.spinbox_morph_kernel_v.value(), self.spinbox_morph_iteration.value()] for i
                           in range(2)}
        settings_values.update({i: [self.spinbox_morph_kernel_h.value(), self.spinbox_morph_kernel_v.value()] for i in range(2, 7)})
        if morph_index in settings_values:
            settings_config['preprocess'][settings_name[morph_index]] = settings_values[morph_index]

        # Save all checked OCR languages
        checked_languages = [language_code for language_code, language_name in tesseract_languages().items()
                             if self.sc_checkbox_dict[language_name].isChecked() and Path('./tessdata', f'{language_code}.traineddata').exists()]
        settings_config['ocr']['language'] = '+'.join(checked_languages)

        # Get the selected language in every Translate To combobox
        google_l = googletrans_languages()
        count = 0
        settings_config['translate']['languages'] = []
        for language_name in tesseract_languages().values():
            if language_name in tesseract_skip_languages():
                continue
            combobox_text = self.translate_to_comboboxes[count].currentText().lower()
            language_code = list(google_l.keys())[list(google_l.values()).index(combobox_text)]
            settings_config['translate']['languages'].append(language_code)
            count += 1

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
