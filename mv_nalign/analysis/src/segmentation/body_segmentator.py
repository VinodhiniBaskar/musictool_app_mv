from mv_nalign import bootstrap as bs
import cv2
from mv_nalign.analysis.src.segmentation.utils import load_graph_model
from mv_nalign.analysis.src.segmentation.evalbody_singleposemodel import get_bodypix_result, get_body_contour
from mv_nalign.analysis.src.segmentation.segments_processing import humanity, group_parts_by_body

DEFAULT_OPTIONS = {
    "segmentation_threshold": 0.7,
    "target_height": 800
}


class BodySegmentator():
    def __init__(self, model_path, options):
        self.graph = load_graph_model(model_path)
        self.options = {**DEFAULT_OPTIONS, **options}

    def get_body_parts(self, img):
        result = get_bodypix_result(self.graph, img, segmentation_threshold=self.options['segmentation_threshold'], target_height=self.options['target_height'])
        body_contour = result["body_contour"]
        grouped_parts = group_parts_by_body(result['body_contour'], result['parts'])
        result = []

        for i in range(len(grouped_parts)):
            hum = humanity(grouped_parts[i])
            x, y, w, h = cv2.boundingRect(body_contour[i])
            result.append((
                body_contour[i],
                grouped_parts[i],
                (x, y, x+w, y+h),
                hum,
                (img.shape[0], img.shape[1])
            ))

        return result

    def get_body(self, img):
        return get_body_contour(self.graph, img, segmentation_threshold=self.options['segmentation_threshold'],
                                target_height=self.options['target_height'])


def create_body_segmentator(model_path=bs.path("var/bodypix_models"), options={}):
    return BodySegmentator(model_path, options)
