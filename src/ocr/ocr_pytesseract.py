# Standard library
import os

# Third-party libraries
from loguru import logger
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from pytesseract import Output
import cv2
import pandas as pd
import pyperclip
import pytesseract


# Source
from src.config.config import load_config

# Set the Tesseract OCR command path
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


class ImageProcessor:
    def __init__(self):

        self.config = load_config()
        self.filename = None
        self.show_formatted_text = None
        self.custom_config = None
        self.filename = None

    def perform_pytesseract_ocr(self, filename):
        try:
            self.filename = filename
            image_path = self.get_image_path()

            # Point to the folder where Tesseract language data is located
            os.environ['TESSDATA_PREFIX'] = './tessdata/'

            if self.config['preferences']['auto_ocr']:
                logger.info(f"Using Pytesseract Version: {pytesseract.get_tesseract_version()}")
                ImageProcessor.preprocess_image(image_path)
                self.get_pytesseract_configuration()

                if self.config['pytesseract']['preserve_interword_spaces']:
                    ocr_text = self.perform_ocr_image_to_data(image_path)
                else:
                    ocr_text = self.perform_ocr_image_to_string(image_path)

                # Copy text to clipboard if possible and not empty
                if self.config['output']['copy_to_clipboard']:
                    if len(ocr_text) != 0:
                        formatted_text = ocr_text.decode('utf-8') if isinstance(ocr_text, bytes) else ocr_text
                        self.copy_to_clipboard(formatted_text)
                        self.show_formatted_text = formatted_text

                if not self.config['output']['auto_save_capture']:
                    self.remove_temp_file(image_path)

        except Exception as e:
            logger.error(f"An error occurred during PyTessaract OCR process: {e}")

        finally:
            logger.info(f"OCR Text\n{self.show_formatted_text}")
            return self.show_formatted_text

    def get_image_path(self):
        save_dir = self.config['output']['output_folder_path']

        if self.config['output']['auto_save_capture']:
            logger.info(f" Image Path: '{save_dir}\\{self.filename}'")
            return save_dir + "\\" + self.filename

        else:
            logger.info(f"Image Path: '{self.filename}'")
            return self.filename

    @staticmethod
    def preprocess_image(image_file):
        logger.info(f"Preprocessing the image '{image_file}' before ocr")
        try:
            with Image.open(image_file) as img:
                img = ImageProcessor.start_preprocess_image(img,
                                                            scale_factor=3.0,
                                                            sharpness_factor=1.5,
                                                            contrast_factor=2.0)
                img.save(image_file)
                logger.success(f"Image preprocessing completed successfully")

        except Exception as e:
            logger.error(f"An error occurred while opening the image '{image_file}' {e}")

    @staticmethod
    def start_preprocess_image(image, scale_factor=None, sharpness_factor=None, contrast_factor=None):
        try:
            # # Apply Gaussian blur to the image
            # image = image.filter(ImageFilter.GaussianBlur(radius=1))
            # # Convert image to grayscale
            # image = image.convert('L')
            # # Invert the colors
            # image = ImageOps.invert(image)

            if scale_factor is not None:
                width, height = image.size
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size)

            if sharpness_factor is not None:
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(sharpness_factor)

            if contrast_factor is not None:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(contrast_factor)

            return image

        except Exception as e:
            logger.error(f"An error occurred while preprocessing the image: {str(e)}")

    def get_pytesseract_configuration(self):
        psmv = str(self.config['pytesseract']['page_segmentation_mode'])
        piws = str(int(self.config['pytesseract']['preserve_interword_spaces']))
        te_char = ""

        if self.config['pytesseract']['detect_digits_only']:
            te_char = " -c tessedit_char_whitelist=0123456789"
        elif self.config['pytesseract']['enable_blacklist_char']:
            bchr = self.config['pytesseract']['blacklist_char']
            te_char = f" -c tessedit_char_blacklist={bchr}"
        elif self.config['pytesseract']['enable_whitelist_char']:
            wchr = self.config['pytesseract']['whitelist_char']
            te_char = f" -c tessedit_char_whitelist={wchr}"

        self.custom_config = r'-l eng --psm ' + psmv + ' --oem 3' + ' -c preserve_interword_spaces=' + piws + te_char
        logger.info(f"Pytesseract configuration ({self.custom_config})")

    def perform_ocr_image_to_string(self, image_path):
        logger.info(f"Performing pytesseract image to string '{image_path}'")
        ocr_text = pytesseract.image_to_string(Image.open(image_path), config=self.custom_config)
        return ocr_text

    # https://stackoverflow.com/questions/61250577
    def perform_ocr_image_to_data(self, image_path):
        img = cv2.imread(image_path, cv2.COLOR_BGR2GRAY)
        gauss = cv2.GaussianBlur(img, (3, 3), 0)

        logger.info(f"Performing pytesseract image to data '{image_path}'")
        # custom_config = r'-l eng --oem 1 --psm 6 -c preserve_interword_spaces=1'
        text = pytesseract.image_to_string(gauss)
        logger.info(f"TEXT --------: {text}")
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
    def copy_to_clipboard(text):
        try:
            pyperclip.copy(text)
            logger.success("Text successfully copied to clipboard using pyperclip")

        except Exception as e:
            logger.error(f"An error occurred while copying text to clipboard: {e}")

    @staticmethod
    def remove_temp_file(image_path):
        try:
            os.remove(image_path)
            logger.success(f"Temporary file successfully removed '{image_path}'")

        except Exception as e:
            logger.error(f"An error occurred while removing temporary file '{image_path}': {e}")
