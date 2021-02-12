import numpy as np
from shapely.geometry import Polygon


def euclidean(v1, v2):
    return sum([(v1[i] - v2[i])**2 for i in range(len(v1))])**0.5


# intersection over area
def ioa(rect1, rect2):
    p1 = Polygon([(rect1[0], rect1[1]), (rect1[2], rect1[1]), (rect1[2], rect1[3]), (rect1[0], rect1[3])])
    p2 = Polygon([(rect2[0], rect2[1]), (rect2[2], rect2[1]), (rect2[2], rect2[3]), (rect2[0], rect2[3])])

    return p1.intersection(p2).area / p2.area


# intersection over union
def iou(rect1, rect2):
    p1 = Polygon([(rect1[0], rect1[1]), (rect1[2], rect1[1]), (rect1[2], rect1[3]), (rect1[0], rect1[3])])
    p2 = Polygon([(rect2[0], rect2[1]), (rect2[2], rect2[1]), (rect2[2], rect2[3]), (rect2[0], rect2[3])])

    return p1.intersection(p2).area / p1.union(p2).area


def vec_angle_cos(v1, v2):
    try:
        value = np.dot(v1, v2)/(np.linalg.norm(v1) * np.linalg.norm(v2))
    except:
        return float('NaN')

    if abs(value) > 1:
        value = np.trunc(value)

    result = np.arccos(value)

    return result


def vec_angle(v1, v2):
    return np.arccos(vec_angle_cos(v1, v2))
