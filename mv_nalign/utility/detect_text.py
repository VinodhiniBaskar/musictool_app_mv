import boto3
import json


class DetectText:

    rek = boto3.client('rekognition')
    roleArn = ''

    def __init__(self, ahs, role, video):
        self.roleArn = role
        self.ahs = ahs
        self.video = video

    def start_text_detection(self):
        response = self.rek.start_text_detection(Video={'S3Object': {'Bucket': self.ahs.bucket, 'Name': self.video}},
                                                  NotificationChannel={'RoleArn': self.roleArn,
                                                                       'SNSTopicArn': self.ahs.snsTopicArn})
        return response['JobId']

    def get_text_detection_results_for_job(self, job_id):
        max_results = 10
        pagination_token = ''
        finished = False

        result = {}
        while not finished:
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

        res_json = json.dumps(result)
        json_object = json.loads(res_json)
        json_formatted_str = json.dumps(json_object, indent=4)
        print(json_formatted_str)
        return res_json
    def run(self):
        self.ahs.create_topic_and_queue()

        job_id = self.start_text_detection()
        if self.ahs.get_sqs_message_success_for_job(job_id):
            res = self.get_text_detection_results_for_job(job_id)

        self.ahs.delete_topic_and_queue()
        return res
