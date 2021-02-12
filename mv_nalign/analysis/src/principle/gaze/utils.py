import cv2
import numpy as np

EYE_NOSE_BB_PAD = 0.5


def align_box(box, w, h, pad=0):
    return [
        max(int(box[0]) - pad, 0),
        max(int(box[1]) - pad, 0),
        min(int(box[2]) + pad, w),
        min(int(box[3]) + pad, h),
    ]


def extract_face_roi(img, eye_nose_points):
    ih, iw = img.shape[:2]
    x, y, w, h = cv2.boundingRect(np.array(eye_nose_points))
    px = round(w * EYE_NOSE_BB_PAD)
    py = round(h * EYE_NOSE_BB_PAD)

    # cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 255))

    x1, y1, x2, y2 = align_box([x - px, y - px, x + w + px, y + h - py*0.5], iw, ih)

    return img[y1:y2+1, x1:x2+1]


def extract_by_bb(img, bb):
    ih, iw = img.shape[:2]
    x1, y1, x2, y2 = align_box(bb, iw, ih, 20)

    return img[y1:y2 + 1, x1:x2 + 1]
