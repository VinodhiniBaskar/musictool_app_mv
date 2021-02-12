import numpy as np
from mv_nalign.analysis.src.principle.gaze.cnn import GazeDetector
from sklearn.cluster import DBSCAN
from scipy.signal import medfilt
from mv_nalign.analysis.src.geometry import iou
from mv_nalign.analysis.src.principle.gaze.provider import AbstractFacesProvider
IOU_THRESHOLD = 0.3
TIME_THRESHOLD = 750


class FaceResult:
    timestamp = 0
    img = 1
    face_box = 2
    conf = 3
    eye_nose_pts = 4


class GazeResult:
    timestamp = 0
    fb_x1 = 1
    fb_y1 = 2
    fb_x2 = 3
    fb_y2 = 4
    gaze_probability = 5
    gaze_decision = 6
    face_cluster = 7
    w = 8,
    h = 9


def face_metric(face1, face2):

    rect1 = face1[GazeResult.fb_x1: GazeResult.fb_y2 + 1]
    rect2 = face2[GazeResult.fb_x1: GazeResult.fb_y2 + 1]
    iou_score = (1 - iou(rect1, rect2)) / (1 - IOU_THRESHOLD)
    dt = np.abs(face1[GazeResult.timestamp] - face2[GazeResult.timestamp])
    time_score = dt / TIME_THRESHOLD

    return max([iou_score, time_score])


def cluster_faces(faces, min_samples):
    model = DBSCAN(eps=1.0, min_samples=min_samples, metric=face_metric)
    model.fit(faces)
    return model.labels_


class AbstractAnalyzer:
    def get_gaze_results(self, faces_provider: AbstractFacesProvider):
        raise NotImplemented()


class Analyzer(AbstractAnalyzer):
    def __init__(self, gaze_detector: GazeDetector, gaze_threshold=0.6, kernel=3):
        self.gaze_detector = gaze_detector
        self.gaze_threshold = gaze_threshold
        if kernel % 2 == 0:
            kernel += 1
        self.kernel = kernel

    async def get_gaze_results(self, faces_provider: AbstractFacesProvider):
        gaze_ts = np.zeros((0, 10))

        for face_data in await faces_provider.get_faces_iterator():
            gaze_prob = self.gaze_detector.detect(face_data[FaceResult.img], face_data[FaceResult.face_box])

            gaze_ts = np.vstack([gaze_ts, np.array([
                face_data[FaceResult.timestamp],
                *face_data[FaceResult.face_box],
                gaze_prob,
                0,
                0,
                face_data[FaceResult.img].shape[1],
                face_data[FaceResult.img].shape[0]
            ])])

        gaze_ts[:, GazeResult.face_cluster] = cluster_faces(gaze_ts, self.kernel)
        clusters = np.unique(gaze_ts[:, GazeResult.face_cluster])

        if self.kernel >= 3:
            for c in clusters:
                mask = gaze_ts[:, GazeResult.face_cluster] == c
                gaze_ts[mask, GazeResult.gaze_probability] = medfilt(gaze_ts[mask, GazeResult.gaze_probability],
                                                                     self.kernel)

        gaze_ts[:, GazeResult.gaze_decision] = gaze_ts[:, GazeResult.gaze_probability] > self.gaze_threshold

        return gaze_ts
