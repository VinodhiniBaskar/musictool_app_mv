from google.cloud import videointelligence, vision
from protobuf_to_dict import protobuf_to_dict
import time
from mv_nalign.analysis.src.async_tools import thread_pool


class DetectLogos:

    @classmethod
    @thread_pool
    def video_run_detection(cls, uri):
        client = videointelligence.VideoIntelligenceServiceClient()

        features = [videointelligence.enums.Feature.LOGO_RECOGNITION]

        print('[%s] Video %s brand detection started...\n' % (time.time(), uri))
        operation = client.annotate_video(input_uri=uri, features=features)
        response = operation.result()
        print('[%s] Video %s brand detection completed.\n' % (time.time(), uri))
        # Get the first response, since we sent only one video.
        annotation_result = response.annotation_results[0]
        return protobuf_to_dict(annotation_result, use_enum_labels=True)

    @classmethod
    @thread_pool
    def image_run_detection(cls, uri):
        """Detects logos in the file located in Google Cloud Storage or on the Web.
        """
        client = vision.ImageAnnotatorClient()
        image = vision.types.Image()
        image.source.image_uri = uri

        print('[%s] Image %s brand detection started...\n' % (time.time(), uri))
        response = client.logo_detection(image=image)
        print('[%s] Image %s brand detection completed.\n' % (time.time(), uri))
        return protobuf_to_dict(response, use_enum_labels=True)

