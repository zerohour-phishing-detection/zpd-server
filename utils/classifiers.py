import warnings

import cv2
import numpy as np
from imageio import imread
from scipy.stats import wasserstein_distance
from skimage.metrics import structural_similarity
from skimage.transform import resize

##
# Globals
##

warnings.filterwarnings("ignore")

# specify resized image sizes
height = 2**10
width = 2**10

##
# Functions
##


def get_img(path, norm_size=True, norm_exposure=False, norm_width=width, norm_height=height):
    """
    Prepare an image for image processing tasks
    """
    # flatten returns a 2d grayscale array
    img = imread(path, mode='L')
    # resizing returns float vals 0:255; convert to ints for downstream tasks
    if norm_size:
        img = resize(img, (norm_height, norm_width), anti_aliasing=True, preserve_range=True)
    if norm_exposure:
        img = normalize_exposure(img)
    return img


def get_histogram(img):
    """
    Get the histogram of an image. For an 8-bit, grayscale image, the
    histogram will be a 256 unit vector in which the nth value indicates
    the percent of the pixels in the image with the given darkness level.
    The histogram's values sum to 1.
    """
    h, w = img.shape
    hist = [0.0] * 256
    for i in range(h):
        for j in range(w):
            hist[img[i, j]] += 1
    return np.array(hist) / (h * w)


def normalize_exposure(img):
    """
    Normalize the exposure of an image.
    """
    img = img.astype(int)
    hist = get_histogram(img)

    # get the sum of vals accumulated by each position in hist
    cdf = np.array([sum(hist[: i + 1]) for i in range(len(hist))])

    # determine the normalization values for each unit of the cdf
    sk = np.uint8(255 * cdf)

    # normalize each position in the output image
    height, width = img.shape
    normalized = np.zeros_like(img)
    for i in range(0, height):
        for j in range(0, width):
            normalized[i, j] = sk[img[i, j]]
    return normalized.astype(int)


def earth_movers_distance(path_a, path_b):
    """
    Measure the Earth Mover's distance between two images
    @args:
            {str} path_a: the path to an image file
            {str} path_b: the path to an image file
    @returns:
            TODO
    """
    img_a = get_img(path_a, norm_exposure=True, norm_height=100, norm_width=100)
    img_b = get_img(path_b, norm_exposure=True, norm_height=100, norm_width=100)
    hist_a = get_histogram(img_a)
    hist_b = get_histogram(img_b)
    return wasserstein_distance(hist_a, hist_b)


def structural_sim(path_a, path_b):
    """
    Measure the structural similarity between two images
    @args:
            {str} path_a: the path to an image file
            {str} path_b: the path to an image file
    @returns:
            {float} a float {-1:1} that measures structural similarity
                    between the input images
    """
    img_a = get_img(path_a)
    img_b = get_img(path_b)

    sim, _ = structural_similarity(img_a, img_b, full=True, data_range=255)
    return sim


def pixel_sim(path_a, path_b):
    """
    Measure the pixel-level similarity between two images
    @args:
            {str} path_a: the path to an image file
            {str} path_b: the path to an image file
    @returns:
            {float} a float {-1:1} that measures structural similarity
                    between the input images
    """
    img_a = get_img(path_a, norm_exposure=True)
    img_b = get_img(path_b, norm_exposure=True)
    return np.sum(np.absolute(img_a - img_b)) / (height * width) / 255


def orb_sim(path_a, path_b):
    """
    Use ORB features to measure image similarity
    @args:
            {str} path_a: the path to an image file
            {str} path_b: the path to an image file
    @returns:
            TODO
    """
    # initialize the ORB feature detector
    orb = cv2.ORB_create()

    # get the images
    img_a = cv2.imread(path_a)
    img_b = cv2.imread(path_b)

    # find the keypoints and descriptors with ORB
    _, desc_a = orb.detectAndCompute(img_a, None)
    _, desc_b = orb.detectAndCompute(img_b, None)

    # initialize the bruteforce matcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    # match.distance is a float between {0:100} - lower means more similar
    matches = bf.match(desc_a, desc_b)
    similar_regions = [i for i in matches if i.distance < 70]
    if len(matches) == 0:
        return 0
    return len(similar_regions) / len(matches)


def rmse(predictions, targets):
    return np.sqrt(((predictions - targets) ** 2).mean())


def compute_dct(path):
    img = cv2.imread(path, 1)

    blue, green, red = cv2.split(img)

    b_imf = np.float32(blue) / 255.0
    b_dst = cv2.dct(b_imf)

    g_imf = np.float32(green) / 255.0
    g_dst = cv2.dct(g_imf)

    r_imf = np.float32(red) / 255.0
    r_dst = cv2.dct(r_imf)

    return (b_dst, g_dst, r_dst)


def dct(path_a, path_b):
    a_blue, a_green, a_red = compute_dct(path_a)
    b_blue, b_green, b_red = compute_dct(path_b)

    blue_rmse = rmse(a_blue, b_blue)
    green_rmse = rmse(a_green, b_green)
    red_rmse = rmse(a_red, b_red)
    return (blue_rmse + green_rmse + red_rmse) / 3.0
