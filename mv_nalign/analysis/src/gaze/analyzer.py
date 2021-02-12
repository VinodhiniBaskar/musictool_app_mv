import numpy as np
import cv2
from pathlib import Path
import json
import os
from mv_nalign.analysis.src.vid_base_impl.scenarios.faces import Faces
from mv_nalign.analysis.src.gaze.cnn import GazeDetector
from mv_nalign.analysis.src.common import rnd
from typing import Iterable
import pickle
from sklearn.cluster import DBSCAN
from scipy.signal import medfilt
from mv_nalign.analysis.src.geometry import iou
from mv_nalign.analysis.src.aws.provider import AbstractImageProvider, AbstractVideoProvider

IOU_THRESHOLD = 0.3
TIME_THRESHOLD = 750


class FaceResult():
    timestamp = 0
    img = 1
    face_box = 2
    conf = 3
    eye_nose_pts = 4


class AbstractFacesProvider:
    def get_faces_iterator(self) -> Iterable[tuple]:
        raise NotImplemented()

    def get_id(self):
        raise NotImplemented()

    def get_shape(self):
        raise NotImplemented()

    def get_type(self):
        raise NotImplemented()


class AbstractAwsFacesProvider(AbstractFacesProvider):
    def __init__(self, role_arn, bucket, file, cache_path=None):
        self.role_arn = role_arn
        self.bucket = bucket
        self.file = file
        self.cache_path = cache_path
        self.capture = None

    def get_id(self):
        return 'aws-video-%s-%s' % (self.bucket, self.file)

    def _get_faces_recognition_result(self):
        def query_aws():
            analyzer = Faces(self.file, self.bucket, self.role_arn)
            return analyzer.run()

        if self.cache_path is None:
            return query_aws()
        else:
            cached_file_path = '%s/%s_%s.json' % (self.cache_path, self.bucket, Path(self.file).stem)
            if os.path.isfile(cached_file_path):
                with open(cached_file_path, 'r') as f:
                    result = json.load(f)
            else:
                analyzer = Faces(self.file, self.bucket, self.role_arn)
                result = analyzer.run()

                with open(cached_file_path, 'w+') as f:
                    json.dump(result, f)

            return result

    def _get_face_data(self, face, w, h):
        face_box = rnd([
            face['BoundingBox']['Left'] * w,
            face['BoundingBox']['Top'] * h,
            (face['BoundingBox']['Left'] + face['BoundingBox']['Width']) * w,
            (face['BoundingBox']['Top'] + face['BoundingBox']['Height']) * h
        ])

        eye_nose_pts = [
            rnd((m['X'] * w, m['Y'] * h))
            for m in face['Landmarks']
            if m['Type'] in ['eyeLeft', 'eyeRight', 'nose']
        ]

        conf = face['Confidence']

        return face_box, eye_nose_pts, conf


class AwsImageFacesProvider(AbstractAwsFacesProvider):
    def __init__(self, role_arn, bucket, file, image_provider: AbstractImageProvider, cache_path=None):
        super().__init__(role_arn, bucket, file, cache_path)
        self.image_provider = image_provider
        self.img = image_provider.get_image(self.bucket, self.file)

    def get_faces_iterator(self) -> Iterable[tuple]:
        data = self._get_faces_recognition_result()

        for face in data['FaceDetails']:
            face_box, eyes_nose_pts, conf = self._get_face_data(face, self.img.shape[1], self.img.shape[0])
            yield 0, self.img, face_box, conf, eyes_nose_pts

    def shape(self):
        return self.img.shape[:2][::-1]

    def get_type(self):
        return 'image'


class AwsVideoFacesProvider(AbstractAwsFacesProvider):
    def __init__(self, role_arn, bucket, file, video_provider: AbstractVideoProvider, cache_path=None):
        super().__init__(role_arn, bucket, file, cache_path)
        self.capture = video_provider.get_capture(self.bucket, self.file)
        self.shape = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH), self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_faces_iterator(self) -> Iterable[tuple]:
        faces_result = self._get_faces_recognition_result()

        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        w, h = self.shape
        last_t = float('NaN')
        current_frame = None

        for data in faces_result['Faces']:
            # extract data from result
            t = data['Timestamp']
            face_box, eyes_nose_pts, conf = self._get_face_data(data['Face'], w, h)

            # load frame img
            if t != last_t:
                self.capture.set(cv2.CAP_PROP_POS_MSEC, t)
                s, current_frame = self.capture.read()
                if not s:
                    raise Exception(
                        'can\'t read frame at [bucket, file, time]: %s, %s, %0.2f' % (self.bucket, self.file, t))

            last_t = t

            yield t, current_frame, face_box, conf, eyes_nose_pts

    def get_shape(self):
        return self.shape

    def get_type(self):
        return 'video'


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
    def __init__(self, gaze_detector: GazeDetector, cache_path=None, gaze_threshold=0.6, kernel=3):
        self.gaze_detector = gaze_detector
        self.gaze_threshold = gaze_threshold
        if kernel % 2 == 0:
            kernel += 1
        self.kernel = kernel

    def get_gaze_results(self, faces_provider: AbstractFacesProvider):
        gaze_ts = np.zeros((0, 10))

        for face_data in faces_provider.get_faces_iterator():
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


class AnalyzerCache(AbstractAnalyzer):
    def __init__(self, backend: AbstractAnalyzer, cache_path):
        self.backend = backend
        self.cache_path = cache_path

    def get_gaze_results(self, faces_provider: AbstractFacesProvider):
        cached_file_path = '%s/%s.pickle' % (self.cache_path, faces_provider.get_id())
        if os.path.isfile(cached_file_path):
            with open(cached_file_path, 'rb') as f:
                result = pickle.load(f)
        else:
            result = self.backend.get_gaze_results(faces_provider)
            with open(cached_file_path, 'wb+') as f:
                pickle.dump(result, f)

        return result
### 5 - oct -2020 updated