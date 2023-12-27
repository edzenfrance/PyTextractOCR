# Standard library
import imghdr

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
                     enable_grayscale=None,
                     remove_noise=None,
                     enable_deskew=None,
                     deskew_position=None,
                     enable_blurring=None,
                     blurring=None,
                     blur_average_kernel=None,
                     blur_gaussian_kernel=None,
                     blur_median_kernel=None,
                     blur_bilateral_dcs=None,
                     enable_thresholding=None,
                     thresholding=None,
                     threshold_global=None,
                     threshold_global_type=None,
                     threshold_adaptive=None,
                     threshold_adaptive_method=None,
                     enable_morphological_transformation=None,
                     morphological_transformation=None,
                     erosion_kernel_iteration=None,
                     dilation_kernel_iteration=None,
                     opening_kernel=None,
                     closing_kernel=None,
                     gradient_kernel=None,
                     top_hat_kernel=None,
                     black_hat_kernel=None):

    if not enable_preprocess:
        logger.info("Preprocessing is disabled")
        return

    if imghdr.what(image_path) == 'gif':
        logger.warning("The image is a GIF (Graphics Interchange Format). OpenCV does not support GIFs.")
        return

    # Deskew first
    if enable_deskew and deskew_position == 0:
        logger.info("Deskewing image [First]")
        image = io.imread(image_path)
        grayscale = rgb2gray(image)
        angle = determine_skew(grayscale)
        if angle is not None and angle > 0.0:
            rotated = rotate(image, angle, resize=True) * 255
            logger.info(f"Deskew rotated angle value: {angle}")
            io.imsave(image_path, rotated.astype(np.uint8))
        else:
            logger.info("Skipping deskew because rotated angle value is 0.0")

    # Grayscale
    if enable_grayscale or enable_thresholding or remove_noise:
        logger.info("Converting image to grayscale")
        image = cv2.imread(image_path, 0)
    else:
        image = cv2.imread(image_path)

    # Scale Factor
    if scale_factor > 1.0:
        logger.info(f"Resizing image: {scale_factor}x scale")
        image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    # Blurring
    if enable_blurring:
        blurring_methods = {
            0: {"method": cv2.blur, "params": ((blur_average_kernel[0], blur_average_kernel[1]),), "message": "Applying average blur"},
            1: {"method": cv2.GaussianBlur, "params": ((blur_gaussian_kernel[0], blur_gaussian_kernel[1]), 0), "message": "Applying gaussian blur"},
            2: {"method": cv2.medianBlur, "params": (blur_median_kernel,), "message": "Applying median blur"},
            3: {"method": cv2.bilateralFilter, "params": (blur_bilateral_dcs[0], blur_bilateral_dcs[1], blur_bilateral_dcs[2]),
                "message": "Applying bilateral blur"}
        }
        if blurring in blurring_methods:
            method_info = blurring_methods[blurring]
            logger.info(f'{method_info["message"]}: {method_info["params"]}')
            image = method_info["method"](image, *method_info["params"])

    # Remove Noise
    if remove_noise:
        logger.info("Removing noise using global thresholding and connected components with stats")
        _, black_and_white = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)

        nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(black_and_white, None, None, None, 8, cv2.CV_32S)
        sizes = stats[1:, -1]  # get CC_STAT_AREA component
        empty_image = np.zeros(labels.shape, np.uint8)

        for i in range(0, nlabels - 1):
            if sizes[i] >= 100:  # filter small dotted regions
                empty_image[labels == i + 1] = 255

        image = cv2.bitwise_not(empty_image)

    # Thresholding
    if enable_thresholding:
        if thresholding == 0:
            logger.info(f"Applying global thresholding: {threshold_global}")
            _, image = cv2.threshold(image, threshold_global, 255, cv2.THRESH_BINARY)

        elif thresholding == 1:
            logger.info(f"Applying adaptive thresholding {threshold_adaptive}")
            adaptive_method = cv2.ADAPTIVE_THRESH_MEAN_C if threshold_adaptive_method == 0 else cv2.ADAPTIVE_THRESH_GAUSSIAN_C
            image = cv2.adaptiveThreshold(image, 255, adaptive_method, cv2.THRESH_BINARY, threshold_adaptive, 2)

        elif thresholding == 2:
            logger.info("Applying otsu's thresholding")  # Apply Gaussian Blur for best settings
            ret, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            logger.info(f"Otsu thresholding value: {ret}")

    # Morphological Transformation
    if enable_morphological_transformation:
        if morphological_transformation == 0:
            logger.info(f"Applying erosion: {erosion_kernel_iteration}")
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (erosion_kernel_iteration[0], erosion_kernel_iteration[1]))
            image = cv2.erode(image, kernel, iterations=erosion_kernel_iteration[2])

        elif morphological_transformation == 1:
            logger.info(f"Applying dilation: {dilation_kernel_iteration}")
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (dilation_kernel_iteration[0], dilation_kernel_iteration[1]))
            image = cv2.dilate(image, kernel, iterations=dilation_kernel_iteration[2])

        elif morphological_transformation == 2:
            logger.info(f"Applying opening: {opening_kernel}")
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (opening_kernel[0], opening_kernel[1]))
            image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

        elif morphological_transformation == 3:
            logger.info(f"Applying closing: {closing_kernel}")
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (closing_kernel[0], closing_kernel[1]))
            image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)

        elif morphological_transformation == 4:
            logger.info(f"Applying gradient: {gradient_kernel}")
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (gradient_kernel[0], gradient_kernel[1]))
            image = cv2.morphologyEx(image, cv2.MORPH_GRADIENT, kernel)

        elif morphological_transformation == 5:
            logger.info(f"Applying tophat: {top_hat_kernel}")
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (top_hat_kernel[0], top_hat_kernel[1]))
            image = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel)

        elif morphological_transformation == 6:
            logger.info(f"Applying blackhat: {black_hat_kernel}")
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (black_hat_kernel[0], black_hat_kernel[1]))
            image = cv2.morphologyEx(image, cv2.MORPH_BLACKHAT, kernel)

    # Deskew last
    if enable_deskew and deskew_position == 1:
        logger.info(f"Deskewing image [Last]")
        angle = determine_skew(image)
        if angle is not None and angle > 0.0:
            rotated = rotate(image, angle, resize=True) * 255
            logger.info(f"Deskew rotated angle value: {angle}")
            io.imsave(image_path, rotated.astype(np.uint8))
        else:
            logger.info("Skipping deskew because rotated angle value is 0.0")
    else:
        cv2.imwrite(image_path, image)
