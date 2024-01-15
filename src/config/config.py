# Standard library
from pathlib import Path

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
            'enable_grayscale': False,
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
            'threshold_global_type': 0,
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
            'languages': ["en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en",
                          "en", "en", "en", "tl", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en",
                          "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en",
                          "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en",
                          "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en", "en",
                          "en", "en", "en", "en"]
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
        config_path = Path('config.toml')
        if not config_path.is_file():
            with config_path.open('w') as f:
                toml.dump(default_config, f)
            config = default_config
        else:
            config = toml.load(config_path)
    except TomlDecodeError:
        logger.error("An error occurred while loading the configuration file. Using default settings")
        config = default_config

    modified = False
    new_config = {section: {} for section in default_config}  # Create a new dictionary with the same sections as default_config
    for section, section_config in default_config.items():
        if section in config:
            for key in section_config:
                if key in config[section]:
                    new_config[section][key] = config[section][key]  # Update the value from loaded config
                else:
                    logger.warning(f"Missing keys: {[section]}{[key]}")
                    new_config[section][key] = section_config[key]  # If key was not present in loaded config, use the default value
                    modified = True  # If key was not present in loaded config, it's a missing key

    if modified:  # If there was a missing key
        with open("config.toml", "w") as f:
            toml.dump(new_config, f)  # Overwrite the config.toml file with the updated config
    else:
        logger.success("All keys were found in the configuration file")

    return new_config  # Return the updated config


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
