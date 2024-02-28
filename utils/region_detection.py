import math
import os.path
import random
from enum import Enum

import cv2
import numpy as np
import scipy.stats as ss
from pywt import dwt2

# Set up logging
from utils.custom_logger import CustomLogger

main_logger = CustomLogger().main_logger


class RegionData:
    region = None
    index = None
    x = None
    y = None
    unique_colors_count = None
    pct = None
    hierarchy = None
    invert = None
    mean = None
    std = None
    skew = None
    kurtosis = None
    entropy = None
    otsu = None
    energy = None
    occupied_bins = None

    def __init__(
        self,
        region,
        index,
        x,
        y,
        unique_colors_count,
        pct,
        hierarchy,
        invert,
        mean,
        std,
        skew,
        kurtosis,
        entropy,
        otsu,
        energy,
        occupied_bins,
    ):
        self.region = region
        self.index = index
        self.x = x
        self.y = y
        self.unique_colors_count = unique_colors_count
        self.pct = pct
        self.hierarchy = hierarchy
        self.invert = invert
        self.mean = mean
        self.std = std
        self.skew = skew
        self.kurtosis = kurtosis
        self.entropy = entropy
        self.otsu = otsu
        self.energy = energy
        self.occupied_bins = occupied_bins


def _count_colours(image: cv2.typing.MatLike) -> tuple[int, float]:
    """
    Get the number of unique colours and the percentage of the primary colour in the given image.
    """

    # Flatten the image to a 2D array
    flattend_image = image.reshape(-1, image.shape[-1])

    # Get the unique colors and the number of times each appears in the image
    unique_colors, unique_colors_pixels = np.unique(flattend_image, axis=0, return_counts=True)

    primary_color_percentage = (
        np.amax(unique_colors_pixels, initial=0) / max(np.sum(unique_colors_pixels), 1) * 100
    )

    return len(unique_colors), primary_color_percentage


def _draw_regions(
    image: cv2.typing.MatLike,
    image_path: str,
    regions_data: list[RegionData],
    highlight_name: str,
    subregion_draw=False,
):
    """
    Draw the detected regions on the originial image.
    """

    draw_image = np.copy(image)

    for index, region_data in enumerate(regions_data):
        main_logger.debug(f"Drawing region #{index}")

        region_height, region_width, _ = region_data.region.shape
        x = region_data.x
        y = region_data.y

        color_int = random.randint(0, 2)
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
        color = colors[color_int]

        flip = random.randint(0, 1) == 1

        cv2.rectangle(
            draw_image, (x - 5, y - 5), (x + region_width - 5, y + region_height - 5), color, 1
        )

        if region_data.invert:
            text = "-" + str(region_data.index)
        else:
            text = str(region_data.index)

        if flip:
            cv2.putText(
                draw_image,
                text,
                (
                    x + region_width - random.randint(-5, 5),
                    y + region_height - random.randint(-5, 5),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )
        else:
            cv2.putText(
                draw_image,
                text,
                (x - random.randint(-5, 5), y - random.randint(-5, 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

        if subregion_draw:
            cv2.imwrite(
                os.path.join(
                    os.path.dirname(os.path.realpath(image_path)),
                    f"{highlight_name}.subregion.{index}.png",
                ),
                region_data.region,
            )

    cv2.imwrite(
        os.path.join(os.path.dirname(os.path.realpath(image_path)), f"{highlight_name}.png"),
        draw_image,
    )


def _find_regions(
    image: cv2.typing.MatLike, image_path: str, draw: bool, highlight_name: str, invert=True
) -> list["RegionData"]:
    """
    Finds regions in the given image.
    """
    draw_image = np.copy(image)

    contours, hierarchy = _get_contours(image, invert, image_path, draw, highlight_name)

    regions_data = []

    for index, contour in enumerate(contours):
        [x, y, w, h] = cv2.boundingRect(contour)

        # Adding small padding to image for slight context and better search accuracy
        margin = 5
        region_data = image[
            max(0, y - margin) : y + h + margin, max(0, x - margin) : x + w + margin
        ]

        unique_colors_count, pct = _count_colours(region_data)
        # also get a greyscale version of the region for the other attributes
        # (see paper by Evdoxios Baratis and Euripides G.M. Petrakis why this is)

        if region_data.size == 0:
            continue

        r_grey = cv2.cvtColor(region_data, cv2.COLOR_BGR2GRAY)

        # Image info
        mean = np.mean(r_grey, axis=None)
        std = np.std(r_grey, axis=None)
        skew = ss.skew(r_grey, axis=None)
        kurtosis = ss.kurtosis(r_grey, axis=None)
        entropy = ss.entropy(r_grey, axis=None)

        # Otsu threshold
        otsu = 0
        if invert:
            otsu = cv2.threshold(r_grey, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[0]
        else:
            otsu = cv2.threshold(r_grey, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]

        # Energy
        _, (ch, cv, cd) = dwt2(r_grey.T, "db1")
        energy = (ch**2 + cv**2 + cd**2).sum() / r_grey.size

        if math.isnan(energy):
            energy = 0.0

        # Number of shades of grey
        int_hist = cv2.calcHist([r_grey], [0], None, [256], [0, 256]).flatten()
        occupied_bins = np.count_nonzero(int_hist)

        if draw:
            cv2.rectangle(
                draw_image,
                (x - margin, y - margin),
                (x + w + margin, y + h + margin),
                (0, 0, 255),
                1,
            )

        if len(hierarchy) > 0:
            regions_data.append(
                RegionData(
                    region_data,
                    index,
                    x,
                    y,
                    unique_colors_count,
                    pct,
                    hierarchy[0][index],
                    invert,
                    mean,
                    std,
                    skew,
                    kurtosis,
                    entropy,
                    otsu,
                    energy,
                    occupied_bins,
                )
            )
        else:
            regions_data.append(
                RegionData(
                    region_data,
                    index,
                    x,
                    y,
                    unique_colors_count,
                    pct,
                    [-2, -2, -2, -2],
                    invert,
                    mean,
                    std,
                    skew,
                    kurtosis,
                    entropy,
                    otsu,
                    energy,
                    occupied_bins,
                )
            )

    if draw:
        cv2.imwrite(
            os.path.join(os.path.dirname(os.path.realpath(image_path)), f"{highlight_name}.png"),
            draw_image,
        )
        main_logger.debug("Wrote image highlighting the regions to: " + highlight_name)

    return regions_data


def _get_contours(
    image: cv2.typing.MatLike,
    invert: bool,
    image_path: str,
    draw: bool,
    highlight_name: str = "Highlight",
):
    """
    Calculates contours and their hierarchy.
    """

    main_logger.debug("Obtaining grayscale version of image")
    processed_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if draw:
        cv2.imwrite(
            os.path.join(
                os.path.dirname(os.path.realpath(image_path)), f"{highlight_name}-0-grey.png"
            ),
            processed_img,
        )

    main_logger.debug("Thresholding the image")
    if invert:
        cv2.threshold(processed_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU, processed_img)
    else:
        cv2.threshold(processed_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU, processed_img)

    if draw:
        cv2.imwrite(
            os.path.join(
                os.path.dirname(os.path.realpath(image_path)), f"{highlight_name}-1-tresh.png"
            ),
            processed_img,
        )

    main_logger.debug("Dilating")
    processed_img = cv2.dilate(
        processed_img, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 5)), iterations=1
    )

    if draw:
        cv2.imwrite(
            os.path.join(
                os.path.dirname(os.path.realpath(image_path)), f"{highlight_name}-2-dilating.png"
            ),
            processed_img,
        )

    main_logger.debug("Morphing to merge close area's")
    processed_img = cv2.morphologyEx(
        processed_img, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    )

    if draw:
        cv2.imwrite(
            os.path.join(
                os.path.dirname(os.path.realpath(image_path)), f"{highlight_name}-3-inter.png"
            ),
            processed_img,
        )

    main_logger.debug("Eroding")
    processed_img = cv2.erode(
        processed_img, cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4)), iterations=1
    )

    if draw:
        cv2.imwrite(
            os.path.join(
                os.path.dirname(os.path.realpath(image_path)), f"{highlight_name}-4-eroding.png"
            ),
            processed_img,
        )

    main_logger.debug("Finding contours")
    contours, hierarchy = cv2.findContours(processed_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return contours, hierarchy


def _validate_regions(regions_data: list[RegionData]) -> list[RegionData]:
    """
    Filters on the regions, by removing overlapping regions.
    """
    regions_of_interest: list[RegionData] = []

    # TODO check significance of enumeration order, since important (better, more complete) regions may be skipped due to overlap
    for index, region_data in enumerate(regions_data):
        region_height, region_width, _ = region_data.region.shape

        for index2, region_data2 in enumerate(regions_data):
            # Skip the same region. We do not want to compare the same region with itself
            if index == index2:
                continue

            # TODO check proper overlap condition, this will only detect overlap on one quarter
            region_height2, region_width2, _ = region_data2.region.shape
            if region_data.x >= region_data2.x and (
                region_data.x + region_width <= region_data2.x + region_width2
            ):
                # On x axis region1 is contained within region2
                if region_data.y >= region_data2.y and (
                    region_data.y + region_height <= region_data2.y + region_height2
                ):
                    # On y axis region 1 is contained within region2
                    continue

        regions_of_interest.append(region_data)

    return regions_of_interest


class DrawingFlags(Enum):
    FLAG_NO_DRAW = 0
    """Tells the function to **NOT** draw any debugging images."""

    FLAG_DRAW = 1
    """Tells the function to draw the regions on the original image."""

    FLAG_DRAW_RECURSIVE = 2
    """Tells the function to draw the regions and the changes applied to the image."""

    FLAG_SUBREGION_DRAW = 3
    """Tells the function to draw the regions and subregions."""

    FLAG_DRAW_ALL = 4
    """Tells the function to draw all the regions, subregions and changes made to the image."""


def find_regions(
    image_path: str, draw_flag=DrawingFlags.FLAG_DRAW, highlight_name="Highlight"
) -> tuple[list[RegionData], tuple[int, int, int]]:
    """
    Finds all the regions of interest in the image and returns the data of the image.

    Args:
        image_path (str): The path (location) of the image.
        draw_flag (int, optional): The flag to tell the function to draw the regions. Defaults to FLAG_DRAW.
        highlight_name (str, optional): The name of the file to save the highlighted image. Defaults to "Highlight".
    """

    draw = draw_flag != DrawingFlags.FLAG_NO_DRAW
    recursive_draw = (
        draw_flag == DrawingFlags.FLAG_DRAW_RECURSIVE or draw_flag == DrawingFlags.FLAG_DRAW_ALL
    )
    subregion_draw = (
        draw_flag == DrawingFlags.FLAG_SUBREGION_DRAW or draw_flag == DrawingFlags.FLAG_DRAW_ALL
    )

    main_logger.debug("Loading image: " + image_path)
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)

    img_data = (_count_colours(image), image.shape[0], image.shape[1])

    regions_data = _find_regions(
        image,
        image_path,
        recursive_draw,
        highlight_name=f"{highlight_name}.allregions.inverted",
        invert=True,
    )
    regions_data += _find_regions(
        image,
        image_path,
        recursive_draw,
        highlight_name=f"{highlight_name}.allregions.not_inverted",
        invert=False,
    )

    regions_of_interest = _validate_regions(regions_data)

    if draw:
        _draw_regions(
            image, image_path, regions_of_interest, f"{highlight_name}.allregions", subregion_draw
        )

    return regions_of_interest, img_data
