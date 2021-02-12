import time
from mv_nalign.analysis.src.data_preloader import PreLoader


class HumanityFocused:
    def __init__(self, preloader: PreLoader):
        self.preloader = preloader

    def run(self):
        items = self.preloader.faces
        # print(items)
        if ("Faces" in items and not len(items["Faces"])) or ("FaceDetails" in items and not len(items["FaceDetails"])):
            data = {}
        else:
            data = postprocessing(items, self.preloader.file_type)
        if self.preloader.file_type == 'img':
            return {
                "ImageResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "ViolationFound": data["ViolationFound"],
                "Boxes": data["Results"]
            }
        else:
            return {
                "VideoResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "Results": data
            }


def postprocessing(faces, file_type):
    print('[%s] Response postprocessing started...\n' % (time.time()))
    if file_type == 'img':
        result = {"ViolationFound": len(faces["FaceDetails"]) > 2, "Results": faces["FaceDetails"]}
        print('[%s] completed.\n' % time.time())
        return result

    cursor_timestamp = faces["Faces"][0]['Timestamp']
    results = [{"Timestamp": cursor_timestamp}]  # all rest key will be added in loop
    i = 0
    boxes = []
    for face in faces["Faces"]:
        if cursor_timestamp != face['Timestamp']:
            if len(boxes) > 2:
                results[i]["ViolationFound"] = True
            else:
                results[i]["ViolationFound"] = False
            i += 1
            boxes = [{"BoundingBox": face["Face"]["BoundingBox"]}]
            results.append({"Timestamp": face['Timestamp'], "Boxes": boxes})
            cursor_timestamp = face['Timestamp']
        else:
            boxes.append({"BoundingBox": face["Face"]["BoundingBox"]})
            results[i]["Boxes"] = boxes
    # check the last item
    if len(boxes) > 2:
        results[i]["ViolationFound"] = True
    else:
        results[i]["ViolationFound"] = False
    print('[%s] completed.\n' % time.time())
    return results
