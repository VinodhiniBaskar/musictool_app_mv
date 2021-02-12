import boto3
import json
import sys
import time
# from mv_nalign.mvschemas.nalign import theNAlignSetFactory

class LabelDetect:

    rek = boto3.client('rekognition', region_name='us-east-2')
    sqs = boto3.client('sqs',region_name='us-east-2')
    sns = boto3.client('sns',region_name='us-east-2')

    roleArn = ''
    bucket = ''
    video = ''
    startJobId = ''

    sqsQueueUrl = ''
    snsTopicArn = ''
    processType = ''

    def __init__(self, role, bucket, video):
        self.roleArn = role
        self.bucket = bucket
        self.video = video

    def get_sqs_message_success(self):

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

                    if rek_message['JobId'] == self.startJobId:
                        job_found = True
                        if rek_message['Status'] == 'SUCCEEDED':
                            succeeded = True

                        self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                                ReceiptHandle=message['ReceiptHandle'])

                    self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                            ReceiptHandle=message['ReceiptHandle'])

        return succeeded

    def start_label_detection(self):
        response = self.rek.start_label_detection(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
                                                  NotificationChannel={'RoleArn': self.roleArn,
                                                                       'SNSTopicArn': self.snsTopicArn})

        self.startJobId = response['JobId']

    def get_label_detection_results(self):
        max_results = 10
        pagination_token = ''
        finished = False

        result = None
        while not finished:
            response = self.rek.get_label_detection(JobId=self.startJobId,
                                                    MaxResults=max_results,
                                                    NextToken=pagination_token,
                                                    SortBy='TIMESTAMP')
            if not result:
                result = response
            else:
                result["Labels"].extend(response["Labels"])

            if 'NextToken' in response:
                pagination_token = response['NextToken']
            else:
                finished = True

        # ---creating section with count of labels for every label block---
        labels = result['Labels']
        cursor_timestamp = labels[0]['Timestamp']
        timestamps = [{"Timestamp": cursor_timestamp, "LabelsCount": 0}]
        for label in labels:
            if cursor_timestamp != label['Timestamp']:
                timestamps.append({"Timestamp": label['Timestamp'], "LabelsCount": 0})
                cursor_timestamp = label['Timestamp']
        for timestamp in timestamps:
            time_sum = sum([1 for d in labels if d['Timestamp'] == timestamp["Timestamp"]])
            timestamp["LabelsCount"] = time_sum

        result["LabelsCounts"] = timestamps
        # ----------

        res_json = json.dumps(result)
        json_object = json.loads(res_json)
        json_formatted_str = json.dumps(json_object, indent=4)
        # print(json_formatted_str)

        return json_formatted_str

    def create_topic_and_queue(self):

        millis = str(int(round(time.time() * 1000)))

        # create topic
        sns_topic_name = "AmazonRekognitionExample" + millis

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


# this is the way you can use it
def main(video):
    # the ARN of an IAM role that gives Amazon Rekognition publishing permissions to the Amazon SNS topic.
    role_arn = 'arn:aws:iam::274822417273:role/AmazonRekognitionServiceRoleCopy'
    
    bucket = 'machine-vantage-inc-videos'
    # video = 'videoplayback.mp4'

    analyzer = LabelDetect(role_arn, bucket, video)
    analyzer.create_topic_and_queue() 

    analyzer.start_label_detection()
    if analyzer.get_sqs_message_success():
        res = analyzer.get_label_detection_results()

    analyzer.delete_topic_and_queue()

    return res

# test launch
if __name__ == "__main__":
    video = 'videoplayback.mp4'
    main(video)
