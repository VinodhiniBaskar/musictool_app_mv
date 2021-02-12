from mv_nalign.analysis.src.async_tools import thread_pool
import cv2
import numpy as np
import boto3
from botocore.client import ClientError
import time
from datetime import datetime
from mv_nalign.analysis.src.common_helper import from_amazon
from mv_nalign.analysis.src.img_base_impl.frame.frame_detection import Frame


class FrameFaces(Frame):

    rek = boto3.client('rekognition')

    frame = None

    aws_boxes = None
    clustered_boxes = []
    points = []
    clustered_points = []

    def __init__(self, frame):
        self.frame = frame

    @thread_pool
    def _frame_detection(self):
        """
        :param frame: numpy array of pixels
        :return:
        """
        print('[%s] Getting faces from Amazon API:\n' % datetime.now().time())
        is_success, _buf_arr = cv2.imencode(".jpg", self.frame)
        f_bytes = _buf_arr.tobytes()

        result_boxes = []
        try:
            aws_result = self.rek.detect_faces(Image={'Bytes': f_bytes}, Attributes=['ALL'])
            if not len(aws_result['FaceDetails']):
                self.aws_boxes = []
            result_boxes.extend(aws_result['FaceDetails'])
            self.aws_boxes = result_boxes
        except ClientError as e:
            self.aws_boxes = result_boxes
            print('[%s] Error: while requesting the Amazon API:\n%s\n' % (time.time(), e.response['Error']))
        except Exception as e:
            self.aws_boxes = result_boxes
            import traceback
            print('[%s] Unexpected!\n%s' % (time.time(), traceback.format_exc()))

    async def get_aws_boxes(self) -> list:
        if self.aws_boxes is None:
            await self._frame_detection()
        return self.aws_boxes

    async def get_points(self) -> np.array:
        pass

    async def get_clustered_points(self) -> np.array:
        pass

    async def get_clustered_boxes(self) -> list:
        clustered_boxes = []
        if self.aws_boxes is None:
            await self._frame_detection()
        for box in self.aws_boxes:
            clustered_boxes.append(from_amazon(box["BoundingBox"]))
        self.clustered_boxes = clustered_boxes
        return self.clustered_boxes
