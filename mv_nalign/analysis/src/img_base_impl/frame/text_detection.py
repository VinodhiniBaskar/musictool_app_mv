from mv_nalign.analysis.src.async_tools import thread_pool
from mv_nalign.analysis.src.frame_slice_helper import get_regions_of_interest
from mv_nalign.analysis.src.clustering_helper import cluster_points, get_box_form_points, cover_box_with_points_grid
import numpy as np
import boto3
from botocore.client import ClientError
import time
import cv2
import asyncio
from datetime import datetime
from mv_nalign.analysis.src.img_base_impl.frame.frame_detection import Frame


class FrameText(Frame):
    rek = boto3.client('rekognition')

    frame = None
    the_coefficient = None

    aws_boxes = []
    clustered_boxes = []
    points = []
    clustered_points = []

    def __init__(self, frame, high_text_density):
        # self.retry_attempts = 0
        self.frame = frame
        self.high_text_density = high_text_density

    @thread_pool
    def _detect_region(self, im_bytes, regions_of_interest=None) -> dict:
        if regions_of_interest:
            res = self.rek.detect_text(Image={'Bytes': im_bytes}, Filters={'RegionsOfInterest': [regions_of_interest]})
        else:
            res = self.rek.detect_text(Image={'Bytes': im_bytes})
        return res

    async def _detect(self, f_bytes):
        result_parts = []
        for region in get_regions_of_interest(self.high_text_density):
            result_part = self._detect_region(f_bytes, region)
            result_parts.append(result_part)
        return await asyncio.gather(*result_parts)

    async def _frame_detection(self):
        """
        :param frame:
        :return:
        """
        print('[%s] Getting Text from Amazon API:\n' % datetime.now().time())
        is_success, _buf_arr = cv2.imencode(".jpg", self.frame)
        f_bytes = _buf_arr.tobytes()

        try:
            aws_result = []
            result_parts = await self._detect(f_bytes)
            for part in result_parts:
                aws_result.extend(part['TextDetections'])

            self.aws_boxes = self.filter_result(aws_result)
        except ClientError as e:
            # if 'ProvisionedThroughputExceededException' == e.response['Error']['Code']:
            #     self.retry_attempts += 1
            print('[%s] Error: while requesting the Amazon API:\n%s\n' % (time.time(), e.response['Error']))
        except Exception as e:
            import traceback
            print('[%s] Unexpected!\n%s' % (time.time(), traceback.format_exc()))

    async def get_aws_boxes(self) -> list:
        if not self.aws_boxes:
            await self._frame_detection()
        # if self.retry_attempts:
        #     time.sleep(30)
        #     await self.frame_detection()
        return self.aws_boxes

    async def get_points(self) -> np.array:
        if not self.points:
            await self.get_aws_boxes()

            width = self.frame.shape[0]
            height = self.frame.shape[1]

            threshold = 0.01
            if width * height > 2000000:
                self.the_coefficient = 4
            elif width * height > 700000:
                self.the_coefficient = 3
            elif width * height > 300000:
                self.the_coefficient = 2
            else:
                self.the_coefficient = 1
            self.points = self.prepare_aws_formatted_points(self.aws_boxes, threshold * self.the_coefficient)
        return self.points

    async def get_clustered_points(self) -> np.array:
        if not self.clustered_points:
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
    def filter_result(cls, text_res_arr):
        res = []
        for i in range(0, len(text_res_arr)):
            if text_res_arr[i]['Type'] == 'WORD':
                res.append(text_res_arr[i])
        return res

    @classmethod
    def prepare_aws_formatted_points(cls, boxes, threshold) -> np.array:
        x = np.empty([0, 2], int)
        if not len(boxes):
            return x
        for txt in boxes:
            box = txt["Geometry"]["BoundingBox"]
            points = cover_box_with_points_grid(
                [box["Left"], box["Top"], box["Left"] + box["Width"], box["Top"] + box["Height"]], threshold)
            x = np.append(x, points, axis=0)
        return x

