
from mv_nalign.analysis.src.segmentation.body_segmentator import create_body_segmentator
from mv_nalign.analysis.src.img_base_impl.principle.principle import Principle

segmentator = create_body_segmentator()


class FamilyInteractions(Principle):

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
    def _is_adult(cls, age_range):
        low_range = 18 - age_range["Low"]
        high_range = age_range["High"] - 18
        if low_range <= 0:
            return 1
        if high_range <= 0:
            return 0
        return int(high_range >= low_range)

    async def _frame_detection(self, timestamp=0):
        faces = await self.preloader.face_img_base[timestamp].get_aws_boxes()
        kids_count = sum(not self._is_adult(person["AgeRange"]) for person in faces)
        adults_count = sum(self._is_adult(person["AgeRange"]) for person in faces)
        return {
                "Timestamp": timestamp,
                "Boxes": faces,
                "ViolationFound": (adults_count < 1) or (kids_count < 1)
        }
