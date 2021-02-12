from mv_nalign.analysis.src.aws_helper_service import AwsHelperService
from mv_nalign.analysis.src.vid_base_impl.detectors.detect_faces import DetectFaces
from mv_nalign.analysis.src.file_type_helper import get_type
import asyncio


class Faces:
    def __init__(self, file, bucket, role_arn):
        self.file = file
        self.bucket = bucket

        aws_service = AwsHelperService(bucket)
        self.face_analyzer = DetectFaces(aws_service, role_arn)

    def run(self):
        if get_type(self.file,self.bucket) == 'img':
            return asyncio.run(self.face_analyzer.image_run_detection(self.file, self.bucket, callback=None))
        else:
            return asyncio.run(self.face_analyzer.video_run_detection(self.file, self.bucket, callback=None))

