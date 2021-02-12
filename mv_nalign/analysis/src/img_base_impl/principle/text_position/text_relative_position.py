from mv_nalign.analysis.src.img_base_impl.principle.principle import Principle
from shapely.geometry import Polygon


class TextObjectsRelative(Principle):

    resource_type = None

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
        object_results = await self.preloader.obj_img_base[timestamp].get_clustered_boxes()
        text_results = await self.preloader.text_img_base[timestamp].get_clustered_boxes()

        result = []
        for r in text_results:
            # If size of text block is too small compared to frame resolution, it's discarded
            if (r[2] - r[0]) * (r[3] - r[1]) < 0.02:
                continue
            rp = Polygon([(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])  # result polygon
            if not len(object_results):
                if not (r[0] >= 0.5 or (r[2] - 0.5) / (0.5 - r[0]) > 0.7):
                    resulting_box = {
                        "BoundingBox": {
                            "Width": r[2] - r[0],
                            "Height": r[3] - r[1],
                            "Left": r[0],
                            "Top": r[1]
                        }
                    }
                    result.append(resulting_box)
            for ro in object_results:
                rop = Polygon([(ro[0], ro[1]), (ro[2], ro[1]), (ro[2], ro[3]), (ro[0], ro[3])])  # result obj polygon
                intersection = rp.intersection(rop)
                # If text intersect with object on 30% no matter if it is left or right side from this object
                if intersection and intersection.area >= rp.area * 0.3:
                    continue
                if intersection and (r[2] >= ro[2] or r[0] >= ro[0]):
                    continue
                if not intersection and r[0] >= 0.5:
                    continue
                if not intersection and (r[2] - 0.5) / (0.5 - r[0]) > 0.7:
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
