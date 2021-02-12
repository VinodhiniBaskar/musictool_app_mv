import numpy as np
import cv2


def process_coords(coords, scale, rnd):
    if type(coords) in [list, tuple, np.ndarray]:
        res = []
        for item in coords:
            res.append(process_coords(item, scale, rnd))

        return tuple(res)
    else:
        res = coords * scale
        if rnd:
            res = int(round(float(res)))

        return res


def rnd(coords, scale=1):
    return process_coords(coords, scale=scale, rnd=True)


def scale(coords, scale, rnd=False):
    return process_coords(coords, scale=scale, rnd=rnd)


def adjust_height(image, height, interp=cv2.INTER_LANCZOS4):
    """
    Resize image to specified 'height' with proportion kipping
    (!) Do not use to resize two images to the same shape. Calculated width can be differ due to rounding
    """
    width = int(np.round(image.shape[1] * height / image.shape[0]))

    return cv2.resize(image, (width, height), interp)


def fill_gaps(x):
    """
    Filling gaps in 1d array
    :param x: np.array
    :return: np.array
    """
    nans = np.isnan(x)
    t = np.arange(x.shape[0])
    if np.count_nonzero(nans) > 0:
        x[nans] = np.interp(t[nans], t[~nans], x[~nans])

    return x
