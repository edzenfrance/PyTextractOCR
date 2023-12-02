# Standard library
from pathlib import Path

# Third-party libraries
import toml
from toml import TomlDecodeError
from loguru import logger


def check_config_keys(default_config, loaded_config):
    missing_keys = set()

    def find_missing_keys(default_dict, loaded_dict, parent_key=""):
        for key, value in default_dict.items():
            if isinstance(value, dict):
                find_missing_keys(value, loaded_dict.get(key, {}), f"{parent_key}.{key}" if parent_key else key)
            elif key not in loaded_dict:
                missing_keys.add(f"{parent_key}.{key}" if parent_key else key)

    find_missing_keys(default_config, loaded_config)

    if missing_keys:
        logger.info("Missing keys in configuration file")
        for key in missing_keys:
            logger.warning(f"{key}")

    else:
        logger.success("All default keys found in configuration file")

    return not missing_keys


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
            'scale_factor': 1.5,
            'grayscale': True,
            'gaussian_blur': False,
            'median_blur': False,
            'remove_noise': False,
            'adaptive_thresholding': False,
            'global_thresholding': False,
            'global_threshold': 64,
            'deskew': False,
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
            'tray_notification_shown': False
        }
    }

    try:
        # logger.info("Loading configuration file 'config.toml'")
        if Path('config.toml').exists():
            config = toml.load('config.toml')
        else:
            config = default_config

    except TomlDecodeError:
        logger.error("An error occurred while loading the configuration file. Using default settings")
        config = default_config

    # Check for missing keys and display the missing keys if any.
    check_config_keys(default_config, config)

    # Update default_config with values from config where necessary.
    for section, section_config in default_config.items():
        if section in config:
            for key, value in section_config.items():
                if key in config[section]:
                    section_config[key] = config[section][key]

    with open("config.toml", "w") as f:
        toml.dump(default_config, f)

    return default_config


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