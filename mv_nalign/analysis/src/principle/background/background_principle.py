import numpy as np
import cv2
from shapely.geometry import Polygon
from mv_nalign.analysis.src.principle.principle import Principle


class BackgroundPrinciple(Principle):

    def run(self):
        if self.preloader.file_type == 'img':
            data = self.img_run_detection()
            data.pop("Timestamp", None)
            return {
                "ImageResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "Results": [data]
            }
        else:
            data = self.video_run_detection()
            series_res = []
            for t in range(0, len(self.preloader.timestamps)):
                series_res.append({
                    "Timestamp": self.preloader.timestamps[t],
                    "ViolationFound": data[t]["ViolationFound"],
                    "Boxes": data[t]["Boxes"]
                })
            return {
                "VideoResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "Results": series_res
            }

    async def _frame_detection(self, timestamp=0):
        """
        :return:
        """
        frame = self.preloader.text_img_base[timestamp].frame
        text_results = await self.preloader.text_img_base[timestamp].get_clustered_boxes()
        result_boxes = []
        # Get count of colours in each box and save result
        for box in text_results:
            violation_score, _box = prepare_arr(frame, box, self.preloader.height, self.preloader.width)
            if violation_score < 0:
                continue
            if violation_score > 1:
                resulting_box = {
                    "Score": float("{:.2f}".format(violation_score)),
                    "BoundingBox": {
                        "Width": _box[2] - _box[0],
                        "Height": _box[3] - _box[1],
                        "Left": _box[0],
                        "Top": _box[1]
                    }
                }
                result_boxes.append(resulting_box)

        return {"ViolationFound": bool(len(result_boxes)), "Boxes": result_boxes}


def get_object_polygons(object_result_boxes):
    object_polygons = []
    for o in object_result_boxes:
        object_polygons.append(Polygon([(o[0], o[1]), (o[2], o[1]), (o[2], o[3]), (o[0], o[3])]))
    return object_polygons


def is_overlapping_object(text_polygon, object_polygons):
    for o in object_polygons:
        intersection = text_polygon.intersection(o)
        if intersection and intersection.area > text_polygon.area * 0.5:
            return True
    return False


def prepare_arr(frame, box, h, w):
    """
    Helper function reducing memory consumption
    :param frame:
    :param box:
    :param h:
    :param w:
    :return:
    """

    # If size of text block is too small compared to frame resolution, it's discarded
    if (box[2] - box[0]) * (box[3] - box[1]) < 0.02:
        return -1, box

    padding = ((box[3] - box[1]) + (box[2] - box[0])) / 30
    _box = [
        box[0] - padding,
        box[1] - padding,
        box[2] + padding,
        box[3] + padding
    ]
    box_pix = frame[
              int(_box[1] * h):int(_box[3] * h),
              int(_box[0] * w):int(_box[2] * w)
              ]
    if not box_pix.shape[0] or not box_pix.shape[1]:
        print('ERROR: can not get box pixels\n')
        return -1, _box

    score = get_score(box_pix)
    # cv2.waitKey()
    return score, _box


VOLUME = 7000
STD_THRESH = 30
GF_THRESH = 20


def get_score(block):
    ar = block.shape[1] / block.shape[0]
    rh = round((VOLUME / ar) ** 0.5)
    rw = round(ar * rh)
    block = cv2.resize(block, (rw, rh), interpolation=cv2.INTER_CUBIC)

    # calc gradient
    sobel_x = np.abs(cv2.Sobel(block, cv2.CV_16S, 1, 0, ksize=3))
    sobel_y = np.abs(cv2.Sobel(block, cv2.CV_16S, 0, 1, ksize=3))
    grad = cv2.addWeighted(sobel_x, 0.5, sobel_y, 0.5, 0)
    grad = np.apply_along_axis(np.mean, 2, grad)
    grad = cv2.convertScaleAbs(grad)
    # cv2.imshow('grad', grad)

    # calc text mask
    grad_thresh = np.quantile(grad, 0.8)

    text_mask = np.zeros(grad.shape, dtype='uint8')
    text_mask[grad >= grad_thresh] = 255

    # dilate text mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_DILATE, kernel, iterations=1)

    # cv2.imshow('text', text_mask)

    # fill in text mask
    contours, hierarchy = cv2.findContours(text_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for i in range(len(contours)):
        color = 255
        cv2.drawContours(text_mask, contours, i, color, cv2.FILLED, cv2.LINE_8, hierarchy, 0)

    # cv2.imshow('text2', text_mask)

    # extend text mask for gradient subtraction (cause gradient always have padding)
    text_mask_ext = cv2.morphologyEx(text_mask, cv2.MORPH_DILATE, kernel, iterations=1)

    # subtract extended text mask from gradient
    grad[text_mask_ext == 255] = 0

    # cv2.imshow('grad2', text_mask)

    # get pixels array without text mask
    pixels = block[text_mask == 0]

    # calc standard deviation of background and avarage gradient
    std = sum([c ** 2 for c in np.std(pixels, axis=0)]) ** 0.5
    gf = np.sum(grad) / pixels.shape[0]
    return std / STD_THRESH + gf / GF_THRESH
