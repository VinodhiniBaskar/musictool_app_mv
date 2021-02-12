from mv_nalign.analysis.src.data_preloader import PreLoader
from mv_nalign.analysis.src.format_helper import format_objects
import time


class CloseProximity:
    def __init__(self, preloader: PreLoader):
        self.preloader = preloader

    def run(self):
        items = self.preloader.faces
        if ("Faces" in items and not len(items["Faces"])) or ("FaceDetails" in items and not len(items["FaceDetails"])):
            data = {}
        else:
            data = postprocessing(items, self.preloader.file_type)
        print("im type",self.preloader.file_type)
        print("im tpyp2", type)
        if self.preloader.file_type == 'img':
            print("im image",data)
            return {
                "ImageResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "ViolationFound": data["ViolationFound"],
                "Results": data["Results"]
            }
        else:
            print("im video",data)
            return {        
                "VideoResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "Results": data
            }


def postprocessing(faces, type):
    print('[%s] Response postprocessing started...\n' % (time.time()))
    if type == 'img':
        print("im pot b")
        result = frame_postprocessing(faces["FaceDetails"])
        print("im results",result)
        print('[%s] completed.\n' % time.time())
        return result

    result = []
    timestamps = []
    timestamps.extend(val["Timestamp"] for val in faces["Faces"])
    timestamps = set(timestamps)
    timestamps = sorted(timestamps)
    faces_formatted = format_objects(faces["Faces"], "Face")

    for timestamp in timestamps:
        res = frame_postprocessing(faces_formatted[timestamp])
        if res:
            res["Timestamp"] = timestamp
            result.append(res)

    print('[%s] completed.\n' % time.time())
    print(result)
    return result


def old_new_frame_postprocessing(faces):
    lack_of_face_proximity = False

    # Sort all faces to make their position in array same as on the image
    faces = sorted(faces, key=lambda x: (x["BoundingBox"]["Left"], x["BoundingBox"]["Width"]))

    face = [
        faces[0]["BoundingBox"]["Left"],
        faces[0]["BoundingBox"]["Top"],
        faces[0]["BoundingBox"]["Left"] + faces[0]["BoundingBox"]["Width"],
        faces[0]["BoundingBox"]["Top"] + faces[0]["BoundingBox"]["Height"]
    ]
    for i in range(1, len(faces)):
        relation = (face[2] - face[0]) / faces[i]["BoundingBox"]["Width"]
        if 0.5 < relation < 1.6:  # if boxes widths are comparable
            x2 = max(face[2], faces[i]["BoundingBox"]["Left"] + faces[i]["BoundingBox"]["Width"])
            x1 = min(face[0], faces[i]["BoundingBox"]["Left"])
            sum_width = x2 - x1
            horizontal_distance = (sum_width - (face[2] - face[0]) - faces[i]["BoundingBox"]["Width"])

            y2 = max(face[3], faces[i]["BoundingBox"]["Top"] + faces[i]["BoundingBox"]["Height"])
            y1 = min(face[1], faces[i]["BoundingBox"]["Top"])
            sum_height = y2 - y1
            vertical_distance = (sum_width - (face[3] - face[1]) - faces[i]["BoundingBox"]["Height"])
            if (horizontal_distance > 0 and sum_width / horizontal_distance < 2.5) \
                    or abs(sum_height / vertical_distance) < 1:
                lack_of_face_proximity = True
                break
            face = [
                faces[i]["BoundingBox"]["Left"],
                faces[i]["BoundingBox"]["Top"],
                faces[i]["BoundingBox"]["Left"] + faces[0]["BoundingBox"]["Width"],
                faces[i]["BoundingBox"]["Top"] + faces[0]["BoundingBox"]["Height"]
            ]

    return {
        "ViolationFound": lack_of_face_proximity,
        "Boxes": faces
    }


def frame_postprocessing(faces):
    all_boxes = [{"BoundingBox": face["BoundingBox"]} for face in faces]
    response_boxes = []

    # Sort all faces to make their position in array same as on the image
    faces = sorted(faces, key=lambda x: (x["BoundingBox"]["Left"], x["BoundingBox"]["Width"]))

    case_boxes = [{"BoundingBox": faces[0]["BoundingBox"]}]
    close_faces_count = 1
    face = [
        faces[0]["BoundingBox"]["Left"],
        faces[0]["BoundingBox"]["Top"],
        faces[0]["BoundingBox"]["Left"] + faces[0]["BoundingBox"]["Width"],
        faces[0]["BoundingBox"]["Top"] + faces[0]["BoundingBox"]["Height"]
    ]
    for i in range(1, len(faces)):
        relation = (face[2] - face[0]) / faces[i]["BoundingBox"]["Width"]
        if 0.5 < relation < 1.6:  # if boxes widths are comparable
            x2 = max(face[2], faces[i]["BoundingBox"]["Left"] + faces[i]["BoundingBox"]["Width"])
            x1 = min(face[0], faces[i]["BoundingBox"]["Left"])
            sum_width = x2 - x1
            horizontal_distance = (sum_width - (face[2] - face[0]) - faces[i]["BoundingBox"]["Width"])

            y2 = max(face[3], faces[i]["BoundingBox"]["Top"] + faces[i]["BoundingBox"]["Height"])
            y1 = min(face[1], faces[i]["BoundingBox"]["Top"])
            sum_height = y2 - y1
            vertical_distance = (sum_width - (face[3] - face[1]) - faces[i]["BoundingBox"]["Height"])
            if (horizontal_distance > 0 and abs(sum_height / vertical_distance) > 1) \
                    or sum_width / horizontal_distance > 2.5:
                case_boxes.append({"BoundingBox": faces[i]["BoundingBox"]})
                close_faces_count += 1
            else:
                if close_faces_count > 2:
                    response_boxes.append(case_boxes)
                case_boxes = [{"BoundingBox": faces[i]["BoundingBox"]}]
                close_faces_count = 1
            face = [
                faces[i]["BoundingBox"]["Left"],
                faces[i]["BoundingBox"]["Top"],
                faces[i]["BoundingBox"]["Left"] + faces[0]["BoundingBox"]["Width"],
                faces[i]["BoundingBox"]["Top"] + faces[0]["BoundingBox"]["Height"]
            ]

    if len(case_boxes) > 2:
        response_boxes.append(case_boxes)

    return {
        "ViolationFound": bool(len(response_boxes)),
        "CloseBoxes": response_boxes,
        "Boxes": all_boxes
    }
