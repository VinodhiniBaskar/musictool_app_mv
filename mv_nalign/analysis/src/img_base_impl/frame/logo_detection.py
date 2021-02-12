from mv_nalign.analysis.src.async_tools import thread_pool
from datetime import datetime
import cv2
from humanfriendly import format_timespan
from mv_nalign.analysis.src.img_base_impl.frame.frame_detection import Frame
from google.cloud import vision
import time


class FrameLogos(Frame):

    client = vision.ImageAnnotatorClient()

    frame = None
    the_coefficient = None

    google_boxes = None
    filtered_boxes = []

    def __init__(self, frame):
        self.frame = frame

    @thread_pool
    def _frame_detection(self):
        """
        :param frame: numpy array of pixels
        :return:
        """
        # print('[%s] Getting logos from Google API:\n' % time.time())
        print('[%s] Getting logos from Google API:\n' % datetime.now().time())
        is_success, _buf_arr = cv2.imencode(".jpg", self.frame)
        content = _buf_arr.tobytes()

        result_boxes = []
        image = vision.types.Image(content=content)

        response = self.client.logo_detection(image=image)
        logos = response.logo_annotations
        for logo in logos:
            result_boxes.append(self.get_normalized_bounding_box(logo))

        self.google_boxes = result_boxes

        if response.error.message:
            self.aws_boxes = result_boxes
            print('[%s] Error: while requesting the Google API:\n%s\n' % (time.time(), response.error.message))

    async def get_google_boxes(self) -> list:
        if self.google_boxes is None:
            await self._frame_detection()
        return self.google_boxes

    def get_normalized_bounding_box(self, obj):
        width = self.frame.shape[0]
        height = self.frame.shape[1]
        return {
            "Width": (obj.bounding_poly.vertices[2].x - obj.bounding_poly.vertices[0].x) / width,
            "Height": (obj.bounding_poly.vertices[2].y - obj.bounding_poly.vertices[0].y) / height,
            "Left": obj.bounding_poly.vertices[0].x / width,
            "Top": obj.bounding_poly.vertices[0].y / height
        }