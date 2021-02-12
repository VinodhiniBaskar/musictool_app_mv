from mv_nalign import bootstrap as bs
import cv2

from mv_nalign.analysis.src.principle.gaze.utils import extract_by_bb
from mv_nalign.analysis.src.principle.gaze.models.v1 import create_model as v1
from mv_nalign.analysis.src.principle.gaze.models.v2 import create_model as v2
from mv_nalign.analysis.src.principle.gaze.models.v3 import create_model as v3
from mv_nalign.analysis.src.principle.gaze.models.v4 import create_model as v4

ARCHS = {
    'v1': v1,
    'v2': v2,
    'v3': v3,
    'v4': v4 # ResNet50 2
}


class GazeDetector():
    def __init__(self, arch, weights_path):
        self.model, self.input_size = ARCHS[arch]()
        self.model.load_weights(weights_path)

    def detect(self, img, face_box=None):
        if face_box:
            img = extract_by_bb(img, face_box)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (self.input_size, self.input_size), interpolation=cv2.INTER_NEAREST)
        img = img / 255
        img = img.reshape((1, *img.shape))

        result_vector = self.model.predict(img)

        return float(result_vector[0][0])


def create_detector():
    arch = bs.GAZE_ARCH
    weights_path = bs.path('var/gaze/%s' % bs.GAZE_MODEL)

    return GazeDetector(arch, weights_path)
