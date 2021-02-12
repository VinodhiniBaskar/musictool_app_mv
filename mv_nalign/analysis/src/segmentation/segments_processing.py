import numpy as np
import cv2
from mv_nalign.analysis.src.segmentation.evalbody_singleposemodel import FRONT_PARTS

GROUP_INTER_THRESH = 0.9
PROPORTIONS_PATTERN = np.array([0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
                                1, 0.3, 0.3, 0.2, 0.2, 0.05, 0.05])



def polyline_length(polyline):
    """
    Length of opened polyline
    :param polyline: array([[x, y], ...])
    :return: float
    """
    d = np.diff(polyline, axis=0).sum(axis=1) ** 2

    return np.sqrt(d.sum())


def contour_length(contour):
    """
    Length of OpenCV contour
    :param contour:
    :return:
    """
    c = np.hstack([contour, contour[0, :, :]])
    p = c.reshape(c.shape[0], 2)

    return polyline_length(p)


def get_cropping_boundary(contour, shape, offset=1):
    """
    Checking cropping of contour
    :param contour: single OpenCV contour
    :param shape: shape of image as tuple (width, height)
    :param offset: allowable offset from the boundary
    :return: list of arrays in the form [[x, y], ...]
    """
    if contour.shape[0] == 0:
        return []

    width, height = shape
    n = contour.shape[0]
    cropped_left = contour[:, :, 0] <= offset
    cropped_right = contour[:, :, 0] >= width - offset
    cropped_top = contour[:, :, 1] <= offset
    cropped_bottom = contour[:, :, 1] >= height - offset
    cropped = np.bitwise_or(
        np.bitwise_or(cropped_left, cropped_right),
        np.bitwise_or(cropped_top, cropped_bottom)
    ).reshape(n)
    if np.count_nonzero(cropped) == 0:
        return []

    valid = np.where(~cropped)[0]
    if valid.shape[0] == 0:
        return [contour.reshape((n, 2))]

    contour = np.roll(contour, -valid[0])
    cropped = np.roll(cropped, -valid[0])

    cropped_parts = []
    group_start = False
    k1 = None
    for i in range(n):
        if cropped[i] and (not group_start):
            group_start = True
            k1 = i
        if (not cropped[i] or i == n - 1) and group_start:
            group_start = False
            k2 = i if i < n - 1 else n
            if k2 > k1:
                cropped_parts.append(contour[k1: k2, :, :].reshape((k2 - k1, 2)))

    return cropped_parts


def check_cropping_parts(body_parts, shape):

    cropped_parts = []
    for key in body_parts.keys():
        for c in body_parts[key]:
            cropped = get_cropping_boundary(c, shape)
            if len(cropped) > 0:
                cropped_parts.append([key, c])

    return cropped_parts


def group_parts_by_body(body_contours, parts_contours):
    grouped = []
    for bc in body_contours:
        group = {key: [] for key in FRONT_PARTS}
        for key in parts_contours:
            for i, pc in enumerate(parts_contours[key]):
                if pc.shape[0] < 3:
                    continue
                m = cv2.moments(pc)
                try:
                    cx = int(m["m10"] / m["m00"])
                    cy = int(m["m01"] / m["m00"])
                except:
                    continue

                if cv2.pointPolygonTest(bc, (cx, cy), False) >= 0:
                    group[key].append(pc)

        grouped.append(group)

    return grouped


def calc_proportions(parts_contours):
    proportions = np.zeros((len(FRONT_PARTS)))
    for key in parts_contours:
        pi = FRONT_PARTS.index(key)
        for i, pc in enumerate(parts_contours[key]):
            area = cv2.contourArea(pc)
            proportions[pi] += area

    if proportions[FRONT_PARTS.index('backbone')] == 0:
        proportions[:] = np.nan
        return proportions

    proportions = proportions / proportions[FRONT_PARTS.index('backbone')]

    return proportions


def humanity(parts_contours):
    proportions = calc_proportions(parts_contours)
    pm = np.vstack([proportions, PROPORTIONS_PATTERN])
    d = np.apply_along_axis(lambda c: c[0] / c[1], 0, pm)

    if not np.isfinite(proportions).all():
        return 0

    # to big part
    if not (d < 5).all():
        return 0

    # to small head
    if not (d[0] > 1/3):
        return 0

    return 1


