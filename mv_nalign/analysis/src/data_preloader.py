from humanfriendly import format_timespan
import cv2
import asyncio
from mv_nalign.analysis.src.file_type_helper import get_type
from mv_nalign.analysis.src.aws.provider import AwsS3Mixin
from mv_nalign.analysis.src.frame.text_detection import FrameText
from mv_nalign.analysis.src.frame.object_detection import FrameObjects
from mv_nalign.analysis.src.frame.face_detection import FrameFaces
from mv_nalign.analysis.src.frame.logo_detection import FrameLogos


class PreLoader:
    def __init__(self, file, bucket, time_step=400):
        self.file = file
        self.bucket = bucket

        self.time_step = time_step

        self.public_aws_path = None
        self.height = 0
        self.width = 0
        self.file_type = None

        self.timestamps = []
        self.text_img_base = {}
        self.obj_img_base = {}
        self.face_img_base = {}
        self.logo_img_base = {}

    def preload(self):
        try:
            m = AwsS3Mixin()
            self.public_aws_path = m.get_object_url(self.bucket, self.file)

            cap = cv2.VideoCapture(self.public_aws_path)
            self.height = cap.get(4)
            self.width = cap.get(3)
            self.file_type = get_type(self.file)
            # Fill self.text_img_base, self.obj_img_base, self.face_img_base with appropriate data providers
            if self.file_type == 'img':
                ret, frame = cap.read()
                self.text_img_base[0] = FrameText(frame, 1)
                self.obj_img_base[0] = FrameObjects(frame)
                self.face_img_base[0] = FrameFaces(frame)
                self.logo_img_base[0] = FrameLogos(frame)
            else:
                asyncio.run(self._frame_series_detection(cap))
        except Exception as e:
            print("During loading recognition data from AWS got:\n%s" % e.args[0])
            return False
        return True

    def update_public_aws_path(self):
        m = AwsS3Mixin()
        self.public_aws_path = m.get_object_url(self.bucket, self.file)

    async def _frame_series_detection(self, cap, high_text_density=0):
        """
        Method for video frames processing
        :param cap: Numpy array. Capture got from cv2.
        :return: tuple
        """
        fps = cap.get(cv2.CAP_PROP_FPS)
        timestamp = 0
        while True:
            frame_no = int(timestamp * fps / 1000)
            cap.set(1, frame_no)
            ret, frame = cap.read()
            if frame is not None:
                self.timestamps.append(timestamp)
                self.text_img_base[timestamp] = FrameText(frame, high_text_density)
                self.obj_img_base[timestamp] = FrameObjects(frame)
                self.face_img_base[timestamp] = FrameFaces(frame)
                self.logo_img_base[timestamp] = FrameLogos(frame)

                await asyncio.gather(
                    self.text_img_base[timestamp].get_aws_boxes(),
                    self.obj_img_base[timestamp].get_aws_boxes(),
                    self.face_img_base[timestamp].get_aws_boxes(),
                    self.logo_img_base[timestamp].get_google_boxes()
                )
            else:
                break
            timestamp += self.time_step





