from src.vid_base_impl.detectors.detect_logos import DetectLogos
from src.helpers.file_type_helper import get_type_gs
import cv2
import asyncio


class LogoIntervention:
    def __init__(self, file, bucket):
        self.file = file
        self.bucket = bucket
        self.logo_analyzer = DetectLogos()

    def run(self):
        gs_path = "gs://%s/%s" % (self.bucket, self.file)
        https_path = "https://storage.googleapis.com/%s/%s" % (self.bucket, self.file)
        if get_type_gs(self.file, self.bucket) == 'img':
            raise ValueError("This scenario doesn't support images")
        items = asyncio.run(self.get_data(gs_path))

        cap = cv2.VideoCapture(https_path)
        width = cap.get(3)
        height = cap.get(4)

        return {
            "BrandsCount": len(items['logo_recognition_annotations']),
            "LogoDetections": postprocessing(items, width, height)
        }

    async def get_data(self, path):
        return await self.logo_analyzer.video_run_detection(path)

   
def to_milli_sec(obj):
    if not("nanos" in obj):
        obj["nanos"] = 0
    if not("seconds" in obj):
        obj["seconds"] = 0
    return obj["nanos"]/1000000 + obj["seconds"]*1000


def iter_tracks(arr, wr, hr):
    result = []

    for i in range(0, len(arr)):
        size_condition = False
        track_end = to_milli_sec(arr[i]["segment"]["end_time_offset"])

        start = None
        box = None
        condition_lost_at = None
        # Search for logos big enough to be worth consideration within segment
        for obj in arr[i]["timestamped_objects"]:
            left_upper = (obj["normalized_bounding_box"]["left"], obj["normalized_bounding_box"]["top"])
            right_bottom = (obj["normalized_bounding_box"]["right"], obj["normalized_bounding_box"]["bottom"])

            if (wr / (right_bottom[0] * wr - left_upper[0] * wr) < 3) or (
                    hr / (right_bottom[1] * hr - left_upper[1] * hr) < 3):
                box = {
                    "Width": obj["normalized_bounding_box"]["right"] - obj["normalized_bounding_box"]["left"],
                    "Height": obj["normalized_bounding_box"]["bottom"] - obj["normalized_bounding_box"]["top"],
                    "Left": obj["normalized_bounding_box"]["left"],
                    "Top": obj["normalized_bounding_box"]["top"]
                }
                if not size_condition:
                    condition_met_at = to_milli_sec(obj["time_offset"])
                    start = {"Timestamp": int(condition_met_at), "BoundingBox": box}
                size_condition = True
            elif size_condition:
                condition_lost_at = to_milli_sec(obj["time_offset"])
        if not condition_lost_at:
            condition_lost_at = track_end
        if size_condition:
            end = {"Timestamp": int(condition_lost_at), "BoundingBox": box}
            result.append([start, end])

    return result


def postprocessing(logos, wr, hr):
    video_len = to_milli_sec(logos["segment"]["end_time_offset"])
    logo_res = []
    for logo in logos["logo_recognition_annotations"]:
        logo_res.append({"Logo": logo["entity"]["description"], "Segments": iter_tracks(logo["tracks"], wr, hr)})
    return logo_res
