import time
from mv_nalign.analysis.src.data_preloader import PreLoader


class FamilyInteractions:
    def __init__(self, preloader: PreLoader):
        self.preloader = preloader

    def run(self):
        items = self.preloader.faces
        if ("Faces" in items and not len(items["Faces"])) or ("FaceDetails" in items and not len(items["FaceDetails"])):
            data = {}
        else:
            data = postprocessing(items, self.preloader.file_type)
        if self.preloader.file_type == 'img':
            return {
                "ImageResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "ViolationFound": data["ViolationFound"],
                "Results": data["Results"]
            }
        else:
            return {
                "VideoResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "ViolationFound": data["ViolationFound"],
                "Results": data["Results"]
            }


def postprocessing(faces, type):
    print('[%s] Response postprocessing started...\n' % (time.time()))
    adults_count = 0
    if type == 'img':
        for face in faces["FaceDetails"]:
            adults_count += int(is_adult(face["AgeRange"]))
        print('[%s] completed.\n' % time.time())
        if adults_count and (len(faces["FaceDetails"]) - adults_count):
            return {"ViolationFound": False, "Results": faces["FaceDetails"]}
        return {"ViolationFound": True, "Results": faces["FaceDetails"]}

    cursor_timestamp = faces["Faces"][0]['Timestamp']
    boxes = []
    results = [{"Timestamp": cursor_timestamp}]  # all rest key will be added in loop
    i = 0  # Used to build indexes for result array
    vid_level_violation = False
    for face in faces["Faces"]:
        if cursor_timestamp != face['Timestamp']:
            adults_count = count_adults(results[i]["Boxes"])
            kids_count = len(results[i]["Boxes"]) - adults_count
            if (adults_count < 1) or (kids_count < 1):
                results[i]["ViolationFound"] = True
                vid_level_violation = True
            else:
                results[i]["ViolationFound"] = False
            i += 1
            face["Face"]["IsAdult"] = is_adult(face["Face"]["AgeRange"])
            boxes = [face["Face"]]
            results.append({
                "Timestamp": face['Timestamp'],
                "Boxes": boxes
            })
            cursor_timestamp = face['Timestamp']
        else:
            face["Face"]["IsAdult"] = is_adult(face["Face"]["AgeRange"])
            boxes.append(face["Face"])
            results[i]["Boxes"] = boxes
    # check the last item
    adults_count = count_adults(results[i]["Boxes"])
    kids_count = len(results[i]["Boxes"]) - adults_count
    if (adults_count < 1) or (kids_count < 1):
        results[i]["ViolationFound"] = True
        vid_level_violation = True
    else:
        results[i]["ViolationFound"] = False

    print('[%s] completed.\n' % time.time())
    return {"ViolationFound": vid_level_violation, "Results": results}


def is_adult(age_range):
    low_range = 18 - age_range["Low"]
    high_range = age_range["High"] - 18
    if low_range <= 0:
        return True
    if high_range <= 0:
        return False
    return high_range >= low_range


def count_adults(boxes):
    c = 0
    for box in boxes:
        c += int(box["IsAdult"])
    return c
