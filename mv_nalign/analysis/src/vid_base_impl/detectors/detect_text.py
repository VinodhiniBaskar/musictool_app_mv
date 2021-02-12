import boto3
from botocore.client import ClientError
import time
from mv_nalign.analysis.exceptions.aws_client_exception import AwsOperationFailedException
from mv_nalign.analysis.src.async_tools import thread_pool
from urllib.request import urlopen


class DetectText:

    rek = boto3.client('rekognition')
    roleArn = ''

    def __init__(self, ahs, role):
        self.roleArn = role
        self.ahs = ahs

    def start_text_detection(self, video, bucket):
        response = self.rek.start_text_detection(Video={'S3Object': {'Bucket': bucket, 'Name': video}},
                                                 NotificationChannel={'RoleArn': self.roleArn,
                                                                      'SNSTopicArn': self.ahs.snsTopicArn})
        return response['JobId']

    def get_text_detection_results_for_job(self, job_id):
        max_results = 10
        pagination_token = ''
        finished = False

        result = {}
        print('[%s] Obtaining text detection results...\n' % time.time())
        while not finished:
            print('.', end=' ', flush=True)
            try:
                response = self.rek.get_text_detection(JobId=job_id,
                                                       MaxResults=max_results,
                                                       NextToken=pagination_token)
                if not result:
                    result["TextModelVersion"] = response["TextModelVersion"]
                    result["VideoMetadata"] = response["VideoMetadata"]
                    result["TextDetections"] = response["TextDetections"]
                else:
                    result["TextDetections"].extend(response["TextDetections"])

                if 'NextToken' in response:
                    pagination_token = response['NextToken']
                else:
                    finished = True
            except ClientError as e:
                print('[%s] Terminated results obtaining due to error.\n' % time.time())
                raise e
        print('[%s] Text detection results delivery completed.\n' % time.time())
        return result

    @thread_pool
    def video_run_detection(self, video, bucket) -> dict:
        res = {}
        print('[%s] Creating queue an topic for text detection task.\n' % time.time())
        self.ahs.create_topic_and_queue()
        try:
            print('[%s] Video %s text detection started...\n' % (time.time(), video))
            job_id = self.start_text_detection(video, bucket)
            if self.ahs.get_sqs_message_success_for_job(job_id):
                print('[%s] Video %s object detection completed.\n' % (time.time(), video))
                res = self.get_text_detection_results_for_job(job_id)
        except ClientError as e:
            print('[%s] Error: while requesting the Amazon API:\n%s\n' % (time.time(), e.response['Error']))
        except AwsOperationFailedException as e:
            print('[%s] Execution failed: while requesting the Amazon API:\n%s\n' % (time.time(), e))
        finally:
            print('[%s] Removing queue %s an topic %s.\n' % (time.time(), self.ahs.sqsQueueUrl, self.ahs.snsTopicArn))
            self.ahs.delete_topic_and_queue()
        return res

    @thread_pool
    def image_run_detection(self, image, bucket) -> dict:
        result = {}
        try:
            print('[%s] Image %s object detection started...\n' % (time.time(), image))
            result = self.rek.detect_text(Image={'S3Object': {'Bucket': bucket, 'Name': image}})
            print('[%s] Image %s object detection completed.\n' % (time.time(), image))

        except ClientError as e:
            print('[%s] Error: while requesting the Amazon API:\n%s\n' % (time.time(), e.response['Error']))
        finally:
            return result

    def build_image_obj(self,  image, bucket, type='S3Object'):
        if type == 'S3Object':
            return {'S3Object': {'Bucket': bucket, 'Name': image}}
        path = 'https://%s.s3.us-east-2.amazonaws.com/%s' % (bucket, image)
        path = path.replace(' ', '+')
        req = urlopen(path)
        res = req.read()
        return {'Bytes': res}
