import threading
# import rest_upload  #custom module
import time
import httplib2
import http.client as httplib
from apiclient.errors import HttpError
import logging
# import boto3
# from botocore.exceptions import ClientError

import random
httplib2.RETRIES = 1


# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
  httplib.IncompleteRead, httplib.ImproperConnectionState,
  httplib.CannotSendRequest, httplib.CannotSendHeader,
  httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
# from main import db
# coll1=db["test_upload_video"]
from pymongo import MongoClient

""" Db initialization """
local=MongoClient()
db=local['test_youtube_db']
coll1=db["test_video_information"]


class UploadThread(threading.Thread):
    def __init__(self, upload_request):
        self.upload_request = upload_request
        
        threading.Thread.__init__(self)

    def run(self):
        # status,response = rest_upload.resumable_upload(self.upload_request)
        # if 'id' in response:
        #     print("upload to db")
        #test purpose
        # status="success"
        # response="completed"
        # time.sleep(30)
        # print("after 30 seconds")
        insert_request=self.upload_request
        
        

        response = None
        error = None
        retry = 0
        while response is None:
            try:
                print ("Uploading file...")
                status, response = insert_request.next_chunk()
                # print(json.dumps(response))
                if response is not None:
                    if 'id' in response:

                        print ("Video id '%s' was successfully uploaded." % response['id'])
                    else:
                        exit("The upload failed with an unexpected response: %s" % response)
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                        e.content)
                else:
                    raise
            except RETRIABLE_EXCEPTIONS as  e:
                error = "A retriable error occurred: %s" % e

        if error is not None:
            print (error)
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print ("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)
        coll1.insert({"status":status,"response":response})
        print(response)
        return status,response

        



       


def  upload_video(upload_request):
    UploadThread(upload_request).start()





# def upload_file_to_s3(self,file_name, bucket, object_name=None):
#     """Upload a file to an S3 bucket

#     :param file_name: File to upload
#     :param bucket: Bucket to upload to
#     :param object_name: S3 object name. If not specified then file_name is used
#     :return: True if file was uploaded, else False
#     """

#     # If S3 object_name was not specified, use file_name
#     if object_name is None:
#         object_name = file_name

#     # Upload the file
#     s3_client = boto3.client('s3')
#     try:
#         response = s3_client.upload_file(file_name, bucket, object_name)
#     except ClientError as e:
#         logging.error(e)
#         return False
#     return True