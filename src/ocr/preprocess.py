# Third-party libraries
import cv2
import numpy as np
from deskew import determine_skew
from loguru import logger
from skimage import io
from skimage.color import rgb2gray
from skimage.transform import rotate


def preprocess_image(image_path, config):
    try:
        scale_factor = config['preprocess']['scale_factor']
        grayscale = config['preprocess']['grayscale']
        gaussian_blur = config['preprocess']['gaussian_blur']
        median_blur = config['preprocess']['median_blur']
        remove_noise = config['preprocess']['remove_noise']
        adaptive_thresholding = config['preprocess']['adaptive_thresholding']
        adaptive_threshold = config['preprocess']['adaptive_threshold']
        global_thresholding = config['preprocess']['global_thresholding']
        global_threshold = config['preprocess']['global_threshold']
        dilate = config['preprocess']['dilate']
        erode = config['preprocess']['erode']
        deskew = config['preprocess']['deskew']

        start_preprocess(image_path,
                         scale_factor,
                         grayscale,
                         gaussian_blur,
                         median_blur,
                         remove_noise,
                         adaptive_thresholding,
                         adaptive_threshold,
                         global_thresholding,
                         global_threshold,
                         dilate,
                         erode,
                         deskew)

    except Exception as e:
        logger.error(f"An error occurred while preprocessing the image [{e}]")


def start_preprocess(image_path,
                     scale_factor=None,
                     grayscale=None,
                     gaussian_blur=None,
                     median_blur=None,
                     remove_noise=None,
                     adaptive_thresholding=None,
                     adaptive_threshold=None,
                     global_thresholding=None,
                     global_threshold=None,
                     dilate=None,
                     erode=None,
                     deskew=None):

    image = cv2.imread(image_path)

    if scale_factor != 1.0:
        logger.info(f"Resizing image - scale factor: {scale_factor}")
        image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    if grayscale:
        logger.info("Applying grayscale")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if gaussian_blur:
        logger.info("Applying gaussian blur")
        image = cv2.GaussianBlur(image, (5, 5), 0)

    if median_blur:
        logger.info('Applying median blur')
        image = cv2.medianBlur(image, 1)

    if remove_noise:
        if not grayscale:
            logger.info("Applying grayscale")
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        logger.info("Removing noise")
        _, black_and_white = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)

        nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(black_and_white, None, None, None, 8, cv2.CV_32S)
        sizes = stats[1:, -1]  # get CC_STAT_AREA component
        empty_image = np.zeros((labels.shape), np.uint8)

        for i in range(0, nlabels - 1):
            if sizes[i] >= 50:  # filter small dotted regions
                empty_image[labels == i + 1] = 255

        image = cv2.bitwise_not(empty_image)

    if adaptive_thresholding:
        logger.info("Applying adaptive threshold")
        # image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Fix this
        image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, adaptive_threshold, 2)

    if global_thresholding:
        logger.info("Applying global threshold")
        # image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Fix this
        _, image = cv2.threshold(image, global_threshold, 255, cv2.THRESH_BINARY)

    kernel = np.ones((1, 1), np.uint8)

    if dilate:
        image = cv2.dilate(image, kernel, iterations=1)

    if erode:
        image = cv2.erode(image, kernel, iterations=1)

    cv2.imwrite(image_path, image)

    if deskew:
        logger.info("Deskewing")
        deskew_image(image_path)


def deskew_image(image_path):
    image = io.imread(image_path)
    grayscale = rgb2gray(image)
    angle = determine_skew(grayscale)
    rotated = rotate(image, angle, resize=True) * 255
    io.imsave(image_path, rotated.astype(np.uint8))
