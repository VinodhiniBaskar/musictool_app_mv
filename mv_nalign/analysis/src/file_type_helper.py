from google.cloud import storage


def get_type(file):
    print(file)
    if (file.find('.mp4') + file.find('.mov') + file.find('.mpeg4') + file.find('.avi')) == -4:
        return 'img'
    else:
        print("im vid or not")
        return 'vid'


def get_type_gs(file, bucket):
    client = storage.Client()
    bucket = client.bucket(bucket)
    blob = bucket.get_blob(file)
    if not blob.content_type:
        raise ValueError("Invalid blob. Check bucket name and file name.")
    return check(blob.content_type, file)


def check(ct, file_name):
    # Amazon Rekognition Image currently supports the JPEG and PNG image formats.
    # You can submit images either as an S3 object or as a BYTE ARRAY
    # The supported file formats are .mp4, .mov and .avi. for videos and JPEG or PNG for images

    # The Video Intelligence API supports common video formats,
    # including .MOV, .MPEG4, .MP4, .AVI, and the formats decodable by ffmpeg.
    if ct.find('binary') == 0 and \
            ((file_name.find('.mp4') + file_name.find('.mov') + file_name.find('.mpeg4') + file_name.find('.avi')) == -4):
        return 'img'
    elif ct.find('image') == 0:
        return 'img'
    else:
        return 'vid'
