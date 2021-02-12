import boto3
from botocore.client import ClientError
import time
import asyncio
from src.helpers.async_tools import thread_pool
import cv2


class DetectObjects:

    rek = boto3.client('rekognition')
    roleArn = ''

    @thread_pool
    def frame_detection(self, frame):
        """
        :param frame: numpy array of pixels
        :return:
        """
        is_success, _buf_arr = cv2.imencode(".jpg", frame)
        f_bytes = _buf_arr.tobytes()

        result_boxes = []
        try:
            aws_result = self.rek.detect_labels(Image={'Bytes': f_bytes})
            result_boxes = self.get_person_boxes(aws_result)
        except ClientError as e:
            print('[%s] Error: while requesting the Amazon API:\n%s\n' % (time.time(), e.response['Error']))
        except Exception as e:
            import traceback
            print('[%s] Unexpected!\n%s' % (time.time(), traceback.format_exc()))
        finally:
            return result_boxes

    async def video_run_detection(self, file, bucket):
        """
        If bucket is none, function searches for file locally
        :param file:
        :param bucket:
        :return: tuple
        """
        timestamps = []
        frames = []
        frame_requests = []
        if bucket:
            path = 'https://%s.s3.us-east-2.amazonaws.com/%s' % (bucket, file)
            path = path.replace(' ', '+')
        else:
            path = file
        cap = cv2.VideoCapture(path)

        fps = cap.get(cv2.CAP_PROP_FPS)
        step = 500
        timestamp = 0
        while True:
            frame_no = int(timestamp * fps / 1000)
            cap.set(1, frame_no)
            ret, frame = cap.read()
            if frame is not None:
                timestamps.append(timestamp)
                frames.append(frame)
                frame_requests.append(self.frame_detection(frame))
            else:
                break
            timestamp += step
        results = await asyncio.gather(*frame_requests)

        return timestamps, frames, results

    async def image_run_detection(self, file, bucket):
        """
        :param file:
        :param bucket:
        :return:
        """
        if bucket:
            path = 'https://%s.s3.us-east-2.amazonaws.com/%s' % (bucket, file)
            path = path.replace(' ', '+')
        else:
            path = file
        cap = cv2.VideoCapture(path)

        ret, frame = cap.read()
        result = await self.frame_detection(frame)
        return frame, result

    @classmethod
    def get_person_boxes(cls, arr):
        if not len(arr['Labels']):
            return []
        for a in arr['Labels']:
            if a["Name"] == "Person":
                return a['Instances']
        return []
