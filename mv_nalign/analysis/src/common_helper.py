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


def get_type(file_name):
    if (file_name.find('.mp4') + file_name.find('.mov') + file_name.find('.mpeg4') + file_name.find('.avi')) == -4:
        return 'img'
    else:
        return 'vid'


def from_amazon(obj):
    return [obj['Left'], obj['Top'], obj['Left'] + obj['Width'], obj['Top'] + obj['Height']]


def to_amazon_box(box):
    return {
        'Width': box[0],
        'Height': box[1],
        'Left': box[2] - box[0],
        'Top': box[3] - box[1]
    }


def filter_by_size(boxes, frame_part):
    result_boxes = []
    for box in boxes:

        if box["Width"] * box["Height"] < frame_part:
            continue
        else:
            result_boxes.append(box)
    return result_boxes
