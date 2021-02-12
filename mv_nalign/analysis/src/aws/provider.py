import boto3
import cv2
import sys
import time
import traceback


class AwsS3Mixin:
    def get_object_url(self, bucket, file):
        try:
            s3_client = boto3.client('s3')
            url = s3_client.generate_presigned_url('get_object', Params={
                'Bucket': bucket,
                'Key': file
            }, ExpiresIn=3600)
        except Exception:
            print('[%s] Unexpected!\n%s' % (time.time(), traceback.format_exc()))
            sys.exit(2)

        return url


class AbstractVideoProvider:
    def get_capture(self, bucket, file):
        raise NotImplemented()


class AwsVideoProvider(AbstractVideoProvider, AwsS3Mixin):
    def get_capture(self, bucket, file):
        video_url = self.get_object_url(bucket, file)
        capture = cv2.VideoCapture(video_url)

        return capture


class LocalVideoProvider(AbstractVideoProvider):
    def __init__(self, video_root):
        self.video_root = video_root

    def get_capture(self, bucket, file):
        path = "%s/%s/%s" % (self.video_root, bucket, file)
        return cv2.VideoCapture(path)


class AbstractImageProvider:
    def get_image(self, bucket, file):
        raise NotImplemented()


class AwsImageProvider(AbstractImageProvider, AwsS3Mixin):
    def get_image(self, bucket, file):
        url = self.get_object_url(bucket, file)
        cap = cv2.VideoCapture(url)
        s, img = cap.read()
        if not s:
            raise Exception("Can't read image from S3 bucket: %s, file: %s" % (bucket, file))

        return img


class LocalImageProvider(AbstractImageProvider):
    def __init__(self, images_root):
        self.images_root = images_root

    def get_image(self, bucket, file):
        path = "%s/%s/%s" % (self.images_root, bucket, file)
        return cv2.imread(path)

