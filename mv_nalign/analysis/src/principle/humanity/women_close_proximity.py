from mv_nalign.analysis.src.principle.principle import Principle
from mv_nalign.analysis.src.common_helper import from_amazon


class WomenCloseProximity(Principle):

    def run(self):
        if self.preloader.file_type == 'img':
            data = self.img_run_detection()
            data.pop("Timestamp", None)
            return {
                "ImageResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "Results": [data]
            }
        else:
            data = self.video_run_detection()
            series_res = []
            video_level_violation = False
            for t in range(0, len(self.preloader.timestamps)):
                if data[t]["ViolationFound"]:
                    video_level_violation = True
                series_res.append({
                    "Timestamp": self.preloader.timestamps[t],
                    "ViolationFound": data[t]["ViolationFound"],
                    "Boxes": data[t]["Boxes"]
                })
            return {
                "VideoResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "ViolationFound": video_level_violation,
                "Results": series_res
            }

    @classmethod
    def _are_close(cls, face_box1, face_box2):
        bb = [
            min(face_box1[0], face_box2[0]),
            min(face_box1[1], face_box2[1]),
            max(face_box1[2], face_box2[2]),
            max(face_box1[3], face_box2[3])
        ]
        bb_height = bb[3] - bb[1]
        bb_width = bb[2] - bb[0]
        horizontal_distance = bb_width - (face_box1[2] - face_box1[0]) - (face_box2[2] - face_box2[0])
        vertical_distance = bb_height - (face_box1[3] - face_box1[1]) - (face_box2[3] - face_box2[1])

        if (horizontal_distance < 0 and abs(bb_height / vertical_distance) > 2.5) \
                or (vertical_distance < 0 and bb_width / horizontal_distance > 2.5) \
                or (abs(bb_height / vertical_distance) > 2.5 and bb_width / horizontal_distance > 2.5):
            return True
        return False

    @classmethod
    def _are_comparable(cls, face_box1, face_box2):
        relation = (face_box1[2] - face_box1[0] + face_box1[3] - face_box1[1]) / (face_box2[2] - face_box2[0] + face_box2[3] - face_box2[1])
        if 0.65 < relation < 1.5:
            return True
        return False

    async def _frame_detection(self, timestamp=0):
        faces = await self.preloader.face_img_base[timestamp].get_aws_boxes()
        response_boxes = []
        # Get women faces from all the faces in the array
        faces = list(filter(lambda x: x["Gender"]["Value"] == "Female", faces))
        if not len(faces) > 1:
            return {"ViolationFound": False, "CloseBoxes": response_boxes, "Boxes": faces}
        # Sort all faces to make their position in array same as on the image
        faces = sorted(faces, key=lambda x: (x["BoundingBox"]["Left"], x["BoundingBox"]["Width"]))

        close_faces_count = 1
        face = from_amazon(faces[0]["BoundingBox"])
        for i in range(1, len(faces)):
            next_face = from_amazon(faces[i]["BoundingBox"])
            if self._are_comparable(face, next_face) \
                    and self._are_close(face, next_face):
                close_faces_count += 1

        return {
            "Timestamp": timestamp,
            "ViolationFound": len(faces) == close_faces_count,
            "Boxes": faces
        }
