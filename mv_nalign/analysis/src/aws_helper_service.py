import boto3
import json
import sys
from mv_nalign.analysis.exceptions.aws_client_exception import AwsOperationFailedException
from botocore.client import ClientError
import time


class AwsHelperService:

    sqs = boto3.client('sqs')
    sns = boto3.client('sns')

    sqsQueueUrl = ''
    snsTopicArn = ''

    def get_sqs_message_success_for_job(self, job_id):

        job_found = False
        succeeded = False

        while not job_found:
            sqs_response = self.sqs.receive_message(QueueUrl=self.sqsQueueUrl, MessageAttributeNames=['ALL'],
                                                   MaxNumberOfMessages=10)

            if sqs_response:

                if 'Messages' not in sqs_response:
                    sys.stdout.flush()
                    time.sleep(5)
                    continue

                for message in sqs_response['Messages']:
                    notification = json.loads(message['Body'])
                    rek_message = json.loads(notification['Message'])

                    if rek_message['JobId'] == job_id:
                        job_found = True
                        if rek_message['Status'] == 'SUCCEEDED':
                            succeeded = True
                        if rek_message['Status'] == 'FAILED':
                            raise AwsOperationFailedException('%s: %s' % (rek_message['API'], rek_message['Message']))

                        self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                                ReceiptHandle=message['ReceiptHandle'])

                    self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                            ReceiptHandle=message['ReceiptHandle'])
        return succeeded

    def create_topic_and_queue(self):

        millis = str(int(time.time() * 1000))

        # create topic
        sns_topic_name = "AmazonRekognitionTextTopic" + millis

        topic_response = self.sns.create_topic(Name=sns_topic_name)
        self.snsTopicArn = topic_response['TopicArn']

        # create queue
        sqs_queue_name = "AmazonRekognitionQueue" + millis
        self.sqs.create_queue(QueueName=sqs_queue_name)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqs_queue_name)['QueueUrl']

        attributes = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                AttributeNames=['QueueArn'])['Attributes']

        sqs_queue_arn = attributes['QueueArn']

        # subscribe queue to topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqs_queue_arn)

        # authorize SNS to write queue
        policy = """{{
  "Version":"2012-10-17",
  "Statement":[
    {{
      "Sid":"MyPolicy",
      "Effect":"Allow",
      "Principal" : {{"AWS" : "*"}},
      "Action":"SQS:SendMessage",
      "Resource": "{}",
      "Condition":{{
        "ArnEquals":{{
          "aws:SourceArn": "{}"
        }}
      }}
    }}
  ]
}}""".format(sqs_queue_arn, self.snsTopicArn)

        response = self.sqs.set_queue_attributes(
            QueueUrl=self.sqsQueueUrl,
            Attributes={
                'Policy': policy
            })

    def delete_topic_and_queue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)

    @classmethod
    def create_presigned_url(cls, bucket, object, expiration=3600):
        # Generate a presigned URL for the S3 object
        s3_client = boto3.client('s3')
        try:
            url = s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': bucket,
                                                                'Key': object},
                                                        ExpiresIn=expiration)
        except ClientError as e:
            print('[%s] create_presigned_url error: %s.\n' % (time.time(), e))
            raise e
        # The response contains the presigned URL
        return url
