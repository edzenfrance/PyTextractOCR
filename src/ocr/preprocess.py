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
        start_preprocess(image_path, **config['preprocess'])
    except Exception as e:
        logger.error(f"An error occurred while preprocessing the image [{e}]")


def start_preprocess(image_path,
                     scale_factor=None,
                     grayscale=None,
                     image_smoothing=None,
                     blur_kernel=None,
                     gaussian_blur_kernel=None,
                     median_blur_kernel=None,
                     bilateral_filtering_diameter=None,
                     bilateral_filtering_sigmacolor=None,
                     bilateral_filtering_sigmaspace=None,
                     remove_noise=None,
                     adaptive_thresholding=None,
                     adaptive_threshold=None,
                     global_thresholding=None,
                     global_threshold=None,
                     dilate=None,
                     erode=None,
                     structure_manipulation_kernel=None,
                     structure_manipulation_iteration=None,
                     deskew=None):
    image = cv2.imread(image_path)

    if scale_factor != 1.0:
        logger.info(f"Resizing image - scale factor: {scale_factor}")
        image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    if grayscale:
        logger.info("Applying grayscale")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if gaussian_blur_kernel:
        logger.info("Applying gaussian blur")
        image = cv2.GaussianBlur(image, (gaussian_blur_kernel, gaussian_blur_kernel), 0)

    if median_blur_kernel:
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

    kernel = np.ones((structure_manipulation_kernel, structure_manipulation_kernel), np.uint8)

    if dilate:
        image = cv2.dilate(image, kernel, iterations=structure_manipulation_iteration)

    if erode:
        image = cv2.erode(image, kernel, iterations=structure_manipulation_iteration)

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
