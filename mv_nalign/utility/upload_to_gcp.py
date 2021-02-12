import sys

# [START storage_upload_file]
from google.cloud import storage

def upload_blob(file_path, bucket,file_name):
# def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    # bucket = storage_client.create_bucket('machine-vantage-inc-video')
    # print("Bucket {} created.".format(bucket.name))
    print(file_path,bucket,file_name)
    bucket_name = bucket
    source_file_name = file_path
    destination_blob_name = file_name

    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    return True