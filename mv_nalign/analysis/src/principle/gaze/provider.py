import cv2
from mv_nalign.analysis.src.common_helper import rnd
from typing import Iterable
import numpy as np
import statistics


class AbstractFacesProvider:
    async def get_faces_iterator(self) -> []:
        raise NotImplemented()

    def get_shape(self):
        raise NotImplemented()

    def get_type(self):
        raise NotImplemented()


class AbstractAwsFacesProvider(AbstractFacesProvider):
    def __init__(self, preloader):
        self.preloader = preloader
        self.capture = None

    def _query_aws(self):
        raise NotImplemented()

    async def _get_faces_recognition_result(self):
        result = self._query_aws()
        # Filter faces that are not in focus, as like they are a background
        return await self._filter_back_faces(result)

    async def _filter_back_faces(self, faces):
        result = []
        for timestamp in faces:
            _faces = self._filter_frame(await faces[timestamp].get_aws_boxes())
            for _face in _faces:
                result.append({"Timestamp": timestamp, "Face": _face})
        return result
        # else:
        #     return self._filter_frame(faces["FaceDetails"])

    def _filter_frame(self, faces):
        if not len(faces):
            return []
        result = []
        metrics_arr = np.array([])
        for face in faces:
            metrics_arr = np.append(metrics_arr, face['BoundingBox']['Width'] + face['BoundingBox']['Height'])

        _mean = statistics.mean(metrics_arr)
        for face in faces:
            if face['BoundingBox']['Width'] + face['BoundingBox']['Height'] > 0.8*_mean:
                result.append(face)
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
    def __init__(self, preloader):
        super().__init__(preloader)
        cap = cv2.VideoCapture(preloader.public_aws_path)
        s, self.img = cap.read()

    def _query_aws(self):
        return self.preloader.face_img_base

    async def get_faces_iterator(self) -> []:
        result = []
        data = await self._get_faces_recognition_result()

        for face in data:
            face_box, eyes_nose_pts, conf = self._get_face_data(face["Face"], self.img.shape[1], self.img.shape[0])
            result.append([0, self.img, face_box, conf, eyes_nose_pts])

        return result

    def shape(self):
        return self.img.shape[:2][::-1]

    def get_type(self):
        return 'image'


class AwsVideoFacesProvider(AbstractAwsFacesProvider):
    def __init__(self, preloader):
        super().__init__(preloader)
        self.capture = cv2.VideoCapture(preloader.public_aws_path)
        self.shape = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH), self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def _query_aws(self):
        return self.preloader.face_img_base

    async def get_faces_iterator(self) -> []:
        result = []
        faces_result = await self._get_faces_recognition_result()

        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        w, h = self.shape
        last_t = float('NaN')
        current_frame = None

        for data in faces_result:
            # extract data from result
            t = data['Timestamp']
            face_box, eyes_nose_pts, conf = self._get_face_data(data['Face'], w, h)

            # load frame img
            if t != last_t:
                self.capture.set(cv2.CAP_PROP_POS_MSEC, t)
                s, current_frame = self.capture.read()
                if not s:
                    raise Exception(
                        'can\'t read frame at [url, time]: %s, %0.2f' % (self.preloader.public_aws_path, t))

            last_t = t

            result.append([t, current_frame, face_box, conf, eyes_nose_pts])
        return result

    def get_shape(self):
        return self.shape

    def get_type(self):
        return 'video'