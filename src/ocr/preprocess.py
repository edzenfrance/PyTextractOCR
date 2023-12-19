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
                     enable_preprocess=None,
                     scale_factor=None,
                     grayscale=None,
                     blurring=None,
                     average_blur_kernel=None,
                     gaussian_blur_kernel=None,
                     median_blur_kernel=None,
                     bilateral_blur_diameter=None,
                     bilateral_blur_sigmacolor=None,
                     bilateral_blur_sigmaspace=None,
                     remove_noise=None,
                     thresholding=None,
                     threshold_global=None,
                     threshold_adaptive=None,
                     threshold_adaptive_method=None,
                     morphological_transformation=None,
                     erosion_kernel=None,
                     erosion_iteration=None,
                     dilation_kernel=None,
                     dilation_iteration=None,
                     opening_kernel=None,
                     closing_kernel=None,
                     gradient_kernel=None,
                     deskew=None):
    if not enable_preprocess:
        logger.info("Preprocessing image is disabled")
        return

    image = cv2.imread(image_path)

    if scale_factor != 1.0:
        logger.info(f"Resizing image: {scale_factor}x scale")
        image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    if grayscale:
        logger.info("Applying grayscale")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blurring_methods = {
        0: {"method": cv2.blur, "params": ((average_blur_kernel, average_blur_kernel),), "message": "Applying average blurring"},
        1: {"method": cv2.GaussianBlur, "params": ((gaussian_blur_kernel, gaussian_blur_kernel), 0), "message": "Applying gaussian blurring"},
        2: {"method": cv2.medianBlur, "params": (median_blur_kernel,), "message": "Applying median blurring"},
        3: {"method": cv2.bilateralFilter, "params": (bilateral_blur_diameter, bilateral_blur_sigmacolor, bilateral_blur_sigmaspace),
            "message": "Applying bilateral blurring"}
    }
    if blurring in blurring_methods:
        method_info = blurring_methods[blurring]
        logger.info(method_info["message"])
        image = method_info["method"](image, *method_info["params"])

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

    if thresholding == 0:
        logger.info("Applying global thresholding")
        # image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Fix this
        _, image = cv2.threshold(image, threshold_global, 255, cv2.THRESH_BINARY)

    if thresholding == 1:
        logger.info("Applying adaptive thresholding")
        # image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Fix this
        adaptive_method = None
        if threshold_adaptive_method == 0:
            adaptive_method = cv2.ADAPTIVE_THRESH_MEAN_C
        if threshold_adaptive_method == 1:
            adaptive_method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        image = cv2.adaptiveThreshold(image, 255, adaptive_method, cv2.THRESH_BINARY, threshold_adaptive, 2)

    if thresholding == 2:
        logger.info("Applying otsu thresholding")  # Apply Gaussian Blur for best settings
        ret, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        logger.info(f"Otsu's thresholding value: {ret}")

    # kernel = np.ones((structure_manipulation_kernel, structure_manipulation_kernel), np.uint8)

    if morphological_transformation == 0:
        image = cv2.erode(image, erosion_kernel, iterations=erosion_iteration)

    if morphological_transformation == 1:
        image = cv2.dilate(image, dilation_kernel, iterations=dilation_iteration)

    if morphological_transformation == 2:  # NEEDS GRAYSCALE
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (opening_kernel, opening_kernel))
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

    if morphological_transformation == 3:  # NEEDS GRAYSCALE
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (closing_kernel, closing_kernel))
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)

    if morphological_transformation == 4:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (gradient_kernel, gradient_kernel))
        image = cv2.morphologyEx(image, cv2.MORPH_GRADIENT, kernel)

    cv2.imwrite(image_path, image)

    if deskew:
        logger.info("Deskewing image")
        image = io.imread(image_path)
        grayscale = rgb2gray(image)
        angle = determine_skew(grayscale)
        rotated = rotate(image, angle, resize=True) * 255
        io.imsave(image_path, rotated.astype(np.uint8))
