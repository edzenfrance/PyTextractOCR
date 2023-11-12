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
    logger.info("Loading configuration file 'config.toml'")

    default_config = {
        "preferences": {
            'auto_ocr': True,
            'minimize_system_tray': False,
            'enable_sound': True,
            'sound_file': "assets\\sound\\sound.wav",
        },
        "pytesseract": {
            'page_segmentation_mode': 6,
            'ocr_engine_mode': 3,
            'enable_blacklist_char': False,
            'blacklist_char': "",
            'enable_whitelist_char': False,
            'whitelist_char': "",
            'detect_digits_only': False,
            'preserve_interword_spaces': False,
            'language': "english"
        },
        "output": {
            'copy_to_clipboard': True,
            'show_popup_window': True,
            'auto_save_capture': False,
            'output_folder_path': "",
        },
        "translate": {
            'enable_translation': False,
            'server_timeout': 2000,
            'english': "japanese",
            'french': "english",
            'german': "english",
            'japanese': "english",
            'korean': "english",
            'russian': "english",
            'spanish': "english"
        },
        "ocr_preview": {
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
        "main_position": {
            'position_x': 0,
            'position_y': 0
        }
    }

    try:
        # Attempt to load the existing config if it exists
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

    # logger.debug(f"Configuration: {default_config}")
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