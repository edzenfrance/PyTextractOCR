# Standard library
from pathlib import Path
from collections import OrderedDict

# Third-party libraries
import toml
from loguru import logger
from toml import TomlDecodeError


def load_config():
    default_config = {
        "preferences": {
            'minimize_to_system_tray': False,
            'enable_sound': True,
            'sound_file': "assets\\sound\\sound.wav",
        },
        "ocr": {
            'tesseract_path': "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            'language': "eng",
            'page_segmentation_mode': 6,
            'ocr_engine_mode': 3,
            'preserve_interword_spaces': False,
            'enable_blacklist_char': False,
            'blacklist_char': "",
            'enable_whitelist_char': False,
            'whitelist_char': ""
        },
        "preprocess": {
            'enable_preprocess': False,
            'scale_factor': 1.0,
            'enable_grayscale': True,
            'remove_noise': False,
            'enable_deskew': False,
            'deskew_position': 1,
            'enable_blurring': False,
            'blurring': 0,
            'blur_average_kernel': [3, 3],
            'blur_gaussian_kernel': [3, 3],
            'blur_median_kernel': 3,
            'blur_bilateral_dcs': [1, 75, 75],
            'enable_thresholding': False,
            'thresholding': 0,
            'threshold_global': 64,
            'threshold_adaptive': 31,
            'threshold_adaptive_method': 1,
            'enable_morphological_transformation': False,
            'morphological_transformation': 2,
            'erosion_kernel_iteration': [3, 3, 1],
            'dilation_kernel_iteration': [3, 3, 1],
            'opening_kernel': [5, 5],
            'closing_kernel': [5, 5],
            'gradient_kernel': [5, 5],
            'top_hat_kernel': [13, 5],
            'black_hat_kernel': [13, 5],
        },
        "output": {
            'copy_to_clipboard': True,
            'show_popup_window': True,
            'remove_empty_lines': False,
            'save_captured_image': False,
            'save_enhanced_image': False,
            'output_folder_path': "",
        },
        "translate": {
            'enable_translation': False,
            'server_timeout': 2000,
            'afrikaans': "en",
            'albanian': "en",
            'amharic': "en",
            'arabic': "en",
            'armenian': "en",
            'assamese': "en",
            'azerbaijani': "en",
            'basque': "en",
            'belarusian': "en",
            'bengali': "en",
            'bosnian': "en",
            'bulgarian': "en",
            'burmese': "en",
            'catalan': "en",
            'cebuano': "en",
            'chichewa': "en",
            'chinese (simplified)': "en",
            'chinese (traditional)': "en",
            'corsican': "en",
            'croatian': "en",
            'czech': "en",
            'danish': "en",
            'dutch': "en",
            'english': "ja",
            'esperanto': "en",
            'estonian': "en",
            'filipino': "en",
            'finnish': "en",
            'french': "en",
            'frisian': "en",
            'galician': "en",
            'georgian': "en",
            'german': "en",
            'greek': "en",
            'gujarati': "en",
            'haitian creole': "en",
            'hausa': "en",
            'hawaiian': "en",
            'hebrew': "en",
            'hindi': "en",
            'hmong': "en",
            'hungarian': "en",
            'icelandic': "en",
            'igbo': "en",
            'indonesian': "en",
            'irish': "en",
            'italian': "en",
            'japanese': "en",
            'javanese': "en",
            'kannada': "en",
            'kazakh': "en",
            'khmer': "en",
            'korean': "en",
            'kurdish (kurmanji)': "en",
            'kyrgyz': "en",
            'lao': "en",
            'latin': "en",
            'latvian': "en",
            'lithuanian': "en",
            'luxembourgish': "en",
            'macedonian': "en",
            'malagasy': "en",
            'malay': "en",
            'malayalam': "en",
            'maltese': "en",
            'maori': "en",
            'marathi': "en",
            'mongolian': "en",
            'nepali': "en",
            'norwegian': "en",
            'odia': "en",
            'pashto': "en",
            'persian': "en",
            'polish': "en",
            'portuguese': "en",
            'punjabi': "en",
            'quechua': "en",
            'romanian': "en",
            'russian': "en",
            'sanskrit': "en",
            'samoan': "en",
            'scots gaelic': "en",
            'serbian': "en",
            'southern sotho': "en",
            'shona': "en",
            'sindhi': "en",
            'sinhala': "en",
            'slovak': "en",
            'slovenian': "en",
            'somali': "en",
            'spanish': "en",
            'sundanese': "en",
            'swahili': "en",
            'swedish': "en",
            'tajik': "en",
            'tamil': "en",
            'tatar': "en",
            'telugu': "en",
            'thai': "en",
            'turkish': "en",
            'ukrainian': "en",
            'urdu': "en",
            'uyghur': "en",
            'uzbek': "en",
            'vietnamese': "en",
            'welsh': "en",
            'xhosa': "en",
            'yiddish': "en",
            'yoruba': "en",
            'zulu': "en"
        },
        "ocr_window": {
            'font_name': "Arial",
            'font_size': 12,
            'font_weight': 400,
            'font_style': "Regular",
            'font_strikeout': False,
            'font_underline': False,
            'position_x': 0,
            'position_y': 0,
            'always_on_top': False
        },
        "miscellaneous": {
            'main_window_position_x': 0,
            'main_window_position_y': 0,
            'settings_window_position_x': 0,
            'settings_window_position_y': 0,
            'tray_notification_shown': False
        }
    }

    try:
        if Path('config.toml').exists():
            config = toml.load('config.toml')
        else:
            config = default_config
    except TomlDecodeError:
        logger.error("An error occurred while loading the configuration file. Using default settings")
        config = default_config

    modified = False
    new_config = {section: {} for section in default_config}  # create a new dictionary with the same sections as default_config
    for section, section_config in default_config.items():
        if section in config:
            for key in section_config:
                if key in config[section]:
                    new_config[section][key] = config[section][key]  # update the value from loaded config
                else:
                    logger.warning(f"Missing keys: {[section]}{[key]}")
                    new_config[section][key] = section_config[key]  # if key was not present in loaded config, use the default value
                    modified = True  # if key was not present in loaded config, it's a missing key

    if modified:  # if there was a missing key
        with open("config.toml", "w") as f:
            toml.dump(new_config, f)  # overwrite the config.toml file with the updated config
    else:
        logger.success("All keys were found in the configuration file")

    return new_config  # return the updated config


def update_config(new_config):
    try:
        # Read the existing TOML configuration file
        with open('config.toml', 'r') as f:
            existing_config = toml.load(f)

        # Merge the existing config with the new values
        for section, section_values in new_config.items():
            if section in existing_config:
                existing_config[section].update(section_values)
            else:
                existing_config[section] = section_values

        with open('config.toml', 'w') as f:
            toml.dump(existing_config, f)

        logger.success("Configuration file successfully updated")
    except TomlDecodeError:
        logger.error("An error occurred while updating the configuration file 'config.toml'")