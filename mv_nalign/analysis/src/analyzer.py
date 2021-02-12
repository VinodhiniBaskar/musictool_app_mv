import boto3


class Analyzer:
	def __init__(self):
		self.s3 = boto3.resource('s3')
		# print("im analyzer")
	def run_detection(self, file, bucket, callback):
		# print("run detectin started")

		object_data = self.s3.Object(bucket, file)
		# Amazon Rekognition Image currently supports the JPEG and PNG image formats.
		# You can submit images either as an S3 object or as a BYTE  ARRAY
		# The supported file formats are .mp4, .mov and .avi. for videos and JPEG or PNG for images
		print("found content type",object_data.content_type.find('video'))
		# if object_data.content_type.find('image') == 0:
		#     return self.image_run_detection(file, bucket, callback)
		# if object_data.content_type.find('video') == 0:
		#     return self.video_run_detection(file, bucket, callback)
		if object_data.content_type.find('binary') == 0 \
				and file.find('.mp4') >0 or file.find('.mov') >0 or file.find('.avi') >0:
			return self.video_run_detection(file, bucket, callback)
		else:
			print(callback)
			return self.image_run_detection(file, bucket, callback)
 
	def image_run_detection(self, file, bucket, callback=None):
		pass

	def video_run_detection(self, file, bucket, callback=None):
		pass
