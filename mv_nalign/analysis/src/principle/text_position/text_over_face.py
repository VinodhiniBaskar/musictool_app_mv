from mv_nalign.analysis.src.principle.principle import Principle
from shapely.geometry import Polygon


class TextOverFace(Principle):
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
        text_results = await self.preloader.text_img_base[timestamp].get_clustered_boxes()
        face_results = await self.preloader.face_img_base[timestamp].get_clustered_boxes()
        result = []
        for r in text_results:
            rp = Polygon([(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])  # result polygon
            for ro in face_results:
                rop = Polygon([(ro[0], ro[1]), (ro[2], ro[1]), (ro[2], ro[3]), (ro[0], ro[3])])  # result obj polygon
                intersection = rp.intersection(rop)
                if not intersection or intersection.area < rp.area * 0.1:
                    continue
                resulting_box = {
                    "BoundingBox": {
                        "Width": r[2] - r[0],
                        "Height": r[3] - r[1],
                        "Left": r[0],
                        "Top": r[1]
                    }
                }
                result.append(resulting_box)

        return {"ViolationFound": bool(len(result)), "Boxes": result}
