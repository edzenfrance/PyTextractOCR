# Standard libraries
import os
import math
from typing import Tuple, Union

# Third-party libraries
from deskew import determine_skew
from loguru import logger
from PIL import Image
from pytesseract import Output
import cv2
import numpy as np
import pandas as pd
import pyperclip
import pytesseract

# Source
from src.config.config import load_config
from src.utils.translate import translate_text

# Set the Tesseract OCR command path
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


class ImageProcessor:
    def __init__(self):

        self.config = load_config()
        self.filename = None
        self.extracted_text = None
        self.translated_text = None
        self.custom_config = None
        self.filename = None

    def perform_pytesseract_ocr(self, filename):
        try:
            # Point to the folder where Tesseract language data is located
            os.environ['TESSDATA_PREFIX'] = './tessdata/'
            logger.info(f"Pytesseract version: {pytesseract.get_tesseract_version()}")

            self.filename = filename
            image_path = self.get_image_path()

            if self.config['preferences']['auto_ocr']:
                self.preprocess_image(image_path)
                self.get_pytesseract_configuration()

                if self.config['pytesseract']['preserve_interword_spaces']:
                    ocr_text = self.perform_ocr_image_to_data(image_path)
                else:
                    ocr_text = self.perform_ocr_image_to_string(image_path)

                if self.config['output']['copy_to_clipboard']:
                    if ocr_text:
                        self.copy_to_clipboard(ocr_text)
                        self.extracted_text = ocr_text

                if not self.config['output']['auto_save_capture']:
                    self.remove_temp_file(image_path)

                if self.config['translate']['enable_translation']:
                    if ocr_text:
                        self.translated_text = self.translate_extracted_text(self.extracted_text)

        except Exception as e:
            logger.error(f"An error occurred during Pytesseract OCR process: {e}")

        finally:
            if self.extracted_text is not None:
                logger.info(f"OCR Text:\n{self.extracted_text}\nTranslated Text:\n{self.translated_text}")
            else:
                logger.info("OCR Text is empty")
            return self.extracted_text, self.translated_text

    def get_image_path(self):
        save_dir = self.config['output']['output_folder_path']

        if self.config['output']['auto_save_capture']:
            logger.info(f" Image Path: '{save_dir}\\{self.filename}'")
            return save_dir + "\\" + self.filename
        else:
            logger.info(f"Image Path: '{self.filename}'")
            return self.filename

    def preprocess_image(self, image_file):
        try:
            if self.config['pytesseract']['image_binarization']:
                logger.info("Binarizing the image")
                threshold = self.config['pytesseract']['binarization_threshold']
                ImageProcessor.binarize_image(image_file, threshold)
                logger.success("Binarizing completed")
            if self.config['pytesseract']['image_deskewing']:
                logger.info("Deskewing the image")
                ImageProcessor.deskew_image(image_file)
                logger.success("Deskewing completed")

        except Exception as e:
            logger.error(f"An error occurred while preprocessing the image [{e}]")

    def get_pytesseract_configuration(self):
        psmv = str(self.config['pytesseract']['page_segmentation_mode'])
        piws = str(int(self.config['pytesseract']['preserve_interword_spaces']))
        te_char = ""
        lang_dict = {
            'eng': 'english',
            'fra': 'french',
            'deu': 'german',
            'jpn': 'japanese',
            'kor': 'korean',
            'rus': 'russian',
            'spa': 'spanish'
        }
        search_lang = self.config['pytesseract']['language']
        found_key = [key for key, value in lang_dict.items() if value == search_lang]
        lang_key = ''.join(found_key) if found_key else 'eng'

        if self.config['pytesseract']['enable_blacklist_char']:
            te_char = f" -c tessedit_char_blacklist={self.config['pytesseract']['blacklist_char']}"
        elif self.config['pytesseract']['enable_whitelist_char']:
            te_char = f" -c tessedit_char_whitelist={self.config['pytesseract']['whitelist_char']}"

        self.custom_config = r'-l ' + lang_key + ' --psm ' + psmv + ' --oem 3' + ' -c preserve_interword_spaces=' + piws + te_char
        logger.info(f"Pytesseract configuration: {self.custom_config}")

    def perform_ocr_image_to_string(self, image_path):
        logger.info(f"Performing pytesseract image to string '{image_path}'")
        ocr_text = pytesseract.image_to_string(Image.open(image_path), config=self.custom_config)
        return ocr_text

    # https://stackoverflow.com/questions/61250577
    def perform_ocr_image_to_data(self, image_path):
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gauss = cv2.GaussianBlur(gray, (3, 3), 0)

        logger.info(f"Performing pytesseract image to data '{image_path}'")
        d = pytesseract.image_to_data(gauss, config=self.custom_config, output_type=Output.DICT)
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
            # print(text)
            return text

    @staticmethod
    def binarize_image(image_file, threshold):
        binarize_img = ImageProcessor.binarize(Image.open(image_file), threshold)
        binarize_img.save(image_file)

    # https://www.numpyninja.com/post/optical-character-recognition-ocr-using-py-tesseract-part-1
    @staticmethod
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

    @staticmethod
    def deskew_image(image_file):
        image = cv2.imread(image_file)
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        angle = determine_skew(grayscale)
        rotated = ImageProcessor.rotate(image, angle, (0, 0, 0))
        cv2.imwrite(image_file, rotated)

    @staticmethod
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

    @staticmethod
    def copy_to_clipboard(text):
        try:
            pyperclip.copy(text)
            logger.success("Text successfully copied to clipboard using pyperclip")

        except Exception as e:
            logger.error(f"An error occurred while copying text to clipboard: {e}")

    @staticmethod
    def translate_extracted_text(extracted_text):
        google_trans_text = None
        try:
            google_trans_text = translate_text(extracted_text)
            logger.success("Text successfully translated using google translate")

        except Exception as e:
            logger.error(f"An error occurred while translating text: {e}")

        return google_trans_text

    @staticmethod
    def remove_temp_file(image_path):
        try:
            os.remove(image_path)
            logger.success(f"Temporary file successfully removed '{image_path}'")

        except Exception as e:
            logger.error(f"An error occurred while removing temporary file '{image_path}': {e}")
