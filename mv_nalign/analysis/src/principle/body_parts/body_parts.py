
from mv_nalign.analysis.src.segmentation.evalbody_singleposemodel import adjust_height
from mv_nalign.analysis.src.segmentation.body_segmentator import create_body_segmentator
from mv_nalign.analysis.src.geometry import ioa
from mv_nalign.analysis.src.common_helper import from_amazon
from mv_nalign.analysis.src.principle.principle import Principle

segmentator = create_body_segmentator()


class BodyParts(Principle):

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
            for t in range(0, len(self.preloader.timestamps)):
                series_res.append({
                    "Timestamp": self.preloader.timestamps[t],
                    "ViolationFound": data[t]["ViolationFound"],
                    "Boxes": data[t]["Boxes"]
                })
            return {
                "VideoResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "Results": series_res
            }

    async def _frame_detection(self, timestamp=0):
        """
        :param frame:
        :return:
        """
        frame = self.preloader.obj_img_base[timestamp].frame
        boxes = await self.preloader.obj_img_base[timestamp].get_aws_boxes()
        result = []
        image = adjust_height(frame, 800)
        parts_result = segmentator.get_body_parts(image)

        for j in range(0, len(boxes)):
            for i in range(0, len(parts_result)):
                a = (
                    parts_result[i][2][0] / parts_result[i][4][1],
                    parts_result[i][2][1] / parts_result[i][4][0],
                    parts_result[i][2][2] / parts_result[i][4][1],
                    parts_result[i][2][3] / parts_result[i][4][0]
                )
                ioa_val = ioa(a, from_amazon(boxes[j]['BoundingBox']))
                if (ioa_val > 0.7) and (parts_result[i][3] == 0):
                    result.append(boxes[j])

        return {"ViolationFound": bool(len(result)), "Boxes": result}
