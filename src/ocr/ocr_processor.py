# Standard libraries
import os
import math
import shutil
from typing import Tuple, Union

# Third-party libraries
import cv2
import numpy as np
import pandas as pd
import pyperclip
import pytesseract
from deskew import determine_skew
from loguru import logger
from PIL import Image
from pytesseract import Output

# Source
from src.config.config import load_config
from src.utils.translate import translate_text, language_set

# Set the Tesseract OCR command path
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


def perform_ocr(working_image, datetime):
    # Point to the folder where Tesseract language data is located
    os.environ['TESSDATA_PREFIX'] = './tessdata/'

    config = load_config()
    extracted_text = None
    translated_text = None

    try:
        preprocess_image(working_image, config)
        custom_config = get_pytesseract_configuration(config)

        if config['ocr']['preserve_interword_spaces']:
            ocr_text = perform_ocr_image_to_data(working_image, custom_config)
        else:
            ocr_text = perform_ocr_image_to_string(working_image, custom_config)

        if config['output']['copy_to_clipboard']:
            if ocr_text:
                copy_to_clipboard(ocr_text)
                extracted_text = ocr_text

        if config['output']['save_enhanced_image']:
            folder = config['output']['output_folder_path']
            save_temporary_image(working_image, datetime, folder)
        else:
            remove_temporary_image(working_image)

        if config['translate']['enable_translation']:
            if ocr_text:
                translated_text = translate_extracted_text(extracted_text)

    except Exception as e:
        logger.error(f"An error occurred during OCR process: {e}")

    finally:
        if extracted_text is not None:
            logger.info(f"OCR Text:\n{extracted_text}\nTranslated Text:\n{translated_text}")
        else:
            logger.info("OCR Text is empty")
        return extracted_text, translated_text


def preprocess_image(image_path, config):
    try:
        if config['ocr']['image_binarization']:
            threshold = config['ocr']['binarization_threshold']
            binarize_image(image_path, threshold)
            logger.success("Binarizing completed")
        if config['ocr']['image_deskewing']:
            deskew_image(image_path)
            logger.success("Deskewing completed")

    except Exception as e:
        logger.error(f"An error occurred while preprocessing the image [{e}]")


def get_pytesseract_configuration(config):
    psmv = str(config['ocr']['page_segmentation_mode'])
    piwv = str(int(config['ocr']['preserve_interword_spaces']))

    ocr_lang = config['ocr']['language']
    found_key = [key for key, value in language_set().items() if value == ocr_lang]
    language_key = ''.join(found_key) if found_key else 'eng'

    if config['ocr']['enable_blacklist_char']:
        te_char = f" -c tessedit_char_blacklist={config['ocr']['blacklist_char']}"
    elif config['ocr']['enable_whitelist_char']:
        te_char = f" -c tessedit_char_whitelist={config['ocr']['whitelist_char']}"
    else:
        te_char = ""

    custom_config = r'-l ' + language_key + ' --psm ' + psmv + ' --oem 3' + ' -c preserve_interword_spaces=' + piwv + te_char
    logger.info(f"Pytesseract custom configuration: {custom_config}")
    return custom_config


def perform_ocr_image_to_string(image_path, custom_config):
    logger.info(f"Performing pytesseract image to string '{image_path}'")
    ocr_text = pytesseract.image_to_string(Image.open(image_path), config=custom_config)
    return ocr_text


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


def binarize_image(image_path, threshold):
    logger.info("Binarizing the image")
    binarize_img = binarize(Image.open(image_path), threshold)
    binarize_img.save(image_path)


def binarize(image_to_transform, threshold):
    output_image = image_to_transform.convert("L")  # Convert to greyscale image
    '''
    The threshold value is usually provided as a number between 0 and 255, which is the number of bits in a byte.
    The algorithm for the binarization is pretty simple, go through every pixel in the image and, if it's greater
    than the threshold, turn it all the way up (255), and if it's lower than the threshold, turn it all the way down (0).
    '''
    for x in range(output_image.width):
        for y in range(output_image.height):
            # For the given pixel at w,h, check the value against the threshold
            if output_image.getpixel((x, y)) < threshold:  # Note that the first parameter is actually a tuple object
                output_image.putpixel((x, y), 0)
            else:
                output_image.putpixel((x, y), 255)
    return output_image


def deskew_image(image_path):
    logger.info("Deskewing the image")
    image = cv2.imread(image_path)
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    angle = determine_skew(grayscale)
    rotated = rotate(image, angle, (0, 0, 0))
    cv2.imwrite(image_path, rotated)


def rotate(
        image: np.ndarray, angle: float, background: Union[int, Tuple[int, int, int]]
) -> np.ndarray:
    old_width, old_height = image.shape[:2]
    angle_radian = math.radians(angle)
    width = abs(np.sin(angle_radian) * old_height) + abs(np.cos(angle_radian) * old_width)
    height = abs(np.sin(angle_radian) * old_width) + abs(np.cos(angle_radian) * old_height)

    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    rot_mat[1, 2] += (width - old_width) / 2
    rot_mat[0, 2] += (height - old_height) / 2
    return cv2.warpAffine(image, rot_mat, (int(round(height)), int(round(width))), borderValue=background)


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
        logger.success(f"Temporary image successfully removed '{image_path}'")

    except Exception as e:
        logger.error(f"An error occurred while removing temporary image '{image_path}': {e}")
