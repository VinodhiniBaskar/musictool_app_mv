import cv2
import numpy as np
import boto3
from botocore.client import ClientError
import time
from shapely.geometry import Polygon
from shapely.ops import unary_union
from datetime import datetime
from mv_nalign.analysis.src.async_tools import thread_pool
from mv_nalign.analysis.src.clustering_helper import cluster_points, get_box_form_points, cover_box_with_points_grid
from mv_nalign.analysis.src.common_helper import from_amazon
from mv_nalign.analysis.src.frame.frame_detection import Frame


class FrameObjects(Frame):

    rek = boto3.client('rekognition')

    frame = None
    the_coefficient = None

    aws_boxes = None
    clustered_boxes = []
    points = np.array([])
    clustered_points = np.array([])

    def __init__(self, frame):
        self.frame = frame

    @thread_pool
    def _frame_detection(self):
        """
        :param frame: numpy array of pixels
        :return:
        """

        print('[%s] Getting objects from Amazon API:\n' % datetime.now().time())
        is_success, _buf_arr = cv2.imencode(".jpg", self.frame)
        f_bytes = _buf_arr.tobytes()

        result_boxes = []
        try:
            aws_result = self.rek.detect_labels(Image={'Bytes': f_bytes})
            if not len(aws_result['Labels']):
                self.aws_boxes = result_boxes
            for a in aws_result['Labels']:
                if len(a['Instances']):
                    for inst in a['Instances']:
                        inst["Name"] = a["Name"]
                        result_boxes.append(inst)
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
        if not self.points.any():
            await self.get_aws_boxes()

            width = self.frame.shape[0]
            height = self.frame.shape[1]

            threshold = 0.01
            if (width < 1000) and (height < 1000):
                self.the_coefficient = 2
            else:
                self.the_coefficient = 1
            self.points = self.prepare_aws_formatted_points(self.aws_boxes, threshold * self.the_coefficient)
        return self.points

    async def get_clustered_points(self) -> np.array:
        if not self.clustered_points.any():
            await self.get_points()

            self.clustered_points = cluster_points(self.points, self.the_coefficient)
        return self.clustered_points

    async def get_clustered_boxes(self) -> list:
        if not self.clustered_boxes:
            await self.get_clustered_points()
            result_boxes = []
            for i in range(0, len(self.clustered_points)):
                result_boxes.append(get_box_form_points(self.clustered_points[i]))
            self.clustered_boxes = result_boxes
        return self.clustered_boxes

    @classmethod
    def prepare_aws_formatted_points(cls, boxes, threshold) -> np.array:
        x = np.empty([0, 2], int)
        if not len(boxes):
            return x

        # Create hyper-boxes. Optional part --->
        boxes = sorted(boxes, key=lambda x: x["BoundingBox"]["Left"])
        h_boxes = [from_amazon(boxes[0]["BoundingBox"])]
        for i in range(1, len(boxes)):
            geometry = boxes[i]["BoundingBox"]
            _polygon = Polygon([
                (geometry["Left"], geometry["Top"]),
                (geometry["Left"] + geometry["Width"], geometry["Top"]),
                (geometry["Left"] + geometry["Width"], geometry["Top"] + geometry["Height"]),
                (geometry["Left"], geometry["Top"] + geometry["Height"])
            ])
            intersection_flag = False
            for j in range(0, len(h_boxes)):
                geometry = h_boxes[j]
                polygon = Polygon([
                    (geometry[0], geometry[1]),
                    (geometry[2], geometry[1]),
                    (geometry[2], geometry[3]),
                    (geometry[0], geometry[3])
                ])
                intersection = _polygon.intersects(polygon)
                if intersection:
                    res = unary_union([polygon, _polygon])
                    h_boxes[j] = res.bounds
                    intersection_flag = True

            if not intersection_flag:
                h_boxes.append(_polygon.bounds)
        # <---.

        for h_box in h_boxes:
            points = cover_box_with_points_grid(h_box, threshold)
            x = np.append(x, points, axis=0)
        return x
