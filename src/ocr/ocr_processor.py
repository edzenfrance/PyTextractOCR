# Standard libraries
import os
import shutil
from pathlib import Path

# Third-party libraries
import cv2
import pandas as pd
import pyperclip
import pytesseract
from loguru import logger
from PIL import Image
from pytesseract import Output

# Source
from src.config.config import load_config
from src.utils.translate import translate_text
from src.ocr.preprocess import preprocess_image


def perform_ocr(working_image, datetime):
    config = load_config()
    extracted_text = None
    translated_text = None

    tesseract_path = tesseract_check(config['ocr']['tesseract_path'])
    tessdata_path(config, tesseract_path)

    try:
        preprocess_image(working_image, config)
        custom_config = get_pytesseract_configuration(config, tesseract_path)

        if config['ocr']['preserve_interword_spaces']:
            extracted_text = perform_ocr_image_to_data(working_image, custom_config)
        else:
            extracted_text = perform_ocr_image_to_string(working_image, custom_config)

        if config['output']['remove_empty_lines']:
            extracted_text = "\n".join(line for line in extracted_text.split("\n") if line.strip())

        if config['output']['copy_to_clipboard']:
            if extracted_text:
                copy_to_clipboard(extracted_text)

        if config['output']['save_enhanced_image']:
            folder = config['output']['output_folder_path']
            save_temporary_image(working_image, datetime, folder)
        else:
            remove_temporary_image(working_image)

        if config['translate']['enable_translation']:
            if extracted_text:
                translated_text = translate_extracted_text(extracted_text)

    except Exception as e:
        logger.error(f"An error occurred during OCR process: {e}")

    finally:
        if extracted_text:
            logger.info(f"OCR Text:\n[{extracted_text}]\nTranslated Text:\n{translated_text}")
        else:
            logger.info("OCR Text is empty")
        return extracted_text, translated_text


def get_pytesseract_configuration(config, tesseract_path):
    key = f"-l {config['ocr']['language']} " if config['ocr']['language'] else ""
    psmv = f"--psm {str(config['ocr']['page_segmentation_mode'])} "
    oemv = f"--oem {str(config['ocr']['ocr_engine_mode'])} "
    pisv = "-c preserve_interword_spaces=1 " if config['ocr']['preserve_interword_spaces'] else ""

    if config['ocr']['enable_blacklist_char']:
        te_char = fr"-c tessedit_char_blacklist={config['ocr']['blacklist_char']}"
    elif config['ocr']['enable_whitelist_char']:
        te_char = fr"-c tessedit_char_whitelist={config['ocr']['whitelist_char']}"
    else:
        te_char = ""

    logger.info(f"Pytesseract custom configuration: {key}{psmv}{oemv}{pisv}{te_char}")
    return f"{key}{psmv}{oemv}{pisv}{te_char}"


def perform_ocr_image_to_string(image_path, custom_config):
    logger.info(f"Performing pytesseract image to string: {image_path}")
    return pytesseract.image_to_string(Image.open(image_path), config="--psm 3 --oem 3 -c tessedit_char_blacklist=a")


def perform_ocr_image_to_data(image_path, custom_config):
    logger.info(f"Performing pytesseract image to data '{image_path}'")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gauss = cv2.GaussianBlur(gray, (3, 3), 0)

    d = pytesseract.image_to_data(gauss, config=custom_config, output_type=Output.DICT)
    df = pd.DataFrame(d)

    # Clean up blanks
    df1 = df[(df.conf != '-1') & (df.text != ' ') & (df.text != '')]

    # Sort blocks vertically
    sorted_blocks = df1.groupby('block_num').first().sort_values('top').index.tolist()
    for block in sorted_blocks:
        curr = df1[df1['block_num'] == block]
        sel = curr[curr.text.str.len() > 3]
        char_w = (sel.width / sel.text.str.len()).mean()
        prev_par, prev_line, prev_left = 0, 0, 0
        text = ''
        for ix, ln in curr.iterrows():
            # Add new line when necessary
            if prev_par != ln['par_num']:
                text += '\n'
                prev_par = ln['par_num']
                prev_line = ln['line_num']
                prev_left = 0
            elif prev_line != ln['line_num']:
                text += '\n'
                prev_line = ln['line_num']
                prev_left = 0

            added = 0  # Number of spaces that should be added
            if ln['left'] / char_w > prev_left + 1:
                added = int((ln['left']) / char_w) - prev_left
                text += ' ' * added
            text += ln['text'] + ' '
            prev_left += len(ln['text']) + added + 1
        text += '\n'
        # logger.info(text)
        return text


def copy_to_clipboard(text):
    try:
        pyperclip.copy(text)
        logger.success("Text successfully copied to clipboard using pyperclip")

    except Exception as e:
        logger.error(f"An error occurred while copying text to clipboard: {e}")


def translate_extracted_text(extracted_text):
    google_trans_text = None
    try:
        google_trans_text = translate_text(extracted_text)
        logger.success("Text successfully translated using google translate")

    except Exception as e:
        logger.error(f"An error occurred while translating text: {e}")

    return google_trans_text


def save_temporary_image(image_path, datetime, output_folder_path):
    new_image_path = os.path.join(output_folder_path, f"{datetime}_enhanced.png")
    try:
        shutil.move(image_path, new_image_path)
        logger.info(f"The file '{image_path}' has been moved to '{new_image_path}'")

    except Exception as e:
        logger.error(f"Failed to move the file '{image_path}' to '{new_image_path}: {e}")


def remove_temporary_image(image_path):
    try:
        os.remove(image_path)
        logger.success(f"Temporary image successfully removed: {image_path}")

    except Exception as e:
        logger.error(f"An error occurred while removing temporary image '{image_path}': {e}")


def tesseract_check(tesseract_path):
    if Path(tesseract_path).exists():
        logger.info(f"Tesseract Path: {tesseract_path}")
        pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)
        return tesseract_path
    else:
        logger.error(f"Tesseract installation path not found: {tesseract_path}")
        return None


def tesseract_version():
    return pytesseract.get_tesseract_version()


def tessdata_path(config, tesseract_path):
    os.environ['TESSDATA_PREFIX'] = './tessdata/' if config['ocr']['language'] else f"{tesseract_path.parent}/tessdata"
