# Standard library
import os

# Third-party libraries
from loguru import logger
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import pyperclip
import pytesseract

# Source
from src.config.config import load_config
from src.ocr import ocr_indentation_space

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
        """
        Perform Optical Character Recognition (OCR) on an image using PyTessaract.
        ...
        After performing OCR, it calls another method `show_screenshot_ui()`.
        """
        try:
            self.filename = filename
            image_path = self.get_image_path()

            if self.config['preferences']['auto_ocr']:
                # Perform OCR and convert the text in the image into a string or hOCR format
                ocr_text = self.perform_ocr(image_path)

                # Copy string/hOCR text to clipboard if possible and not empty
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
            # print(f"[perform_pytesseract_ocr]"
            #       f"\n------------------OCR Text------------------\n"
            #       f"\n{self.show_formatted_text}"
            #       f"\n------------------OCR Text------------------")
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
        piws = str(int(self.config['pytesseract']['preserved_interword_spaces']))
        obdg = " -c tessedit_char_whitelist=0123456789" if self.config['pytesseract']['detect_digits_only'] else ""

        self.custom_config = r'-l eng --psm ' + psmv + ' --oem 3' + '-c preserve_interword_spaces=' + piws + obdg
        logger.info(f"Pytesseract config = {self.custom_config}")

    def perform_ocr(self, image_path):
        logger.info(f"Using Pytesseract Version: {pytesseract.get_tesseract_version()}")
        if self.config['preferences']['auto_ocr']:
            # Set the TESSDATA_PREFIX environment variable to point to your tessdata directory
            os.environ['TESSDATA_PREFIX'] = './tessdata/'

            self.get_pytesseract_configuration()

            if self.config['pytesseract']['preserved_interword_spaces']:
                ImageProcessor.preprocess_image(image_path)
                ocr_text = ocr_indentation_space.perform_ocr(image_path)
                return ocr_text

            else:
                ImageProcessor.preprocess_image(image_path)
                logger.info(f"Performing pytesseract image to string '{image_path}'")
                ocr_text = pytesseract.image_to_string(Image.open(image_path), config=self.custom_config)
                return ocr_text

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
            logger.error(f"An error occured while removing temporary file '{image_path}': {e}")
