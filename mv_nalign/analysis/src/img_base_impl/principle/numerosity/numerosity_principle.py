import copy
from shapely.geometry import Polygon
from mv_nalign.analysis.src.img_base_impl.principle.principle import Principle


class NumerosityPrinciple(Principle):

    def run(self):
        if self.preloader.file_type == 'img':
            data = self.img_run_detection()
            return {
                "ImageResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "Results": [
                    {
                        "ViolationFound": len(data) > 3,
                        "Boxes": data
                    }
                ]
            }
        else:
            data = self.video_run_detection()
            series_res = []
            for t in range(0, len(self.preloader.timestamps)):
                res = data[t]
                series_res.append({
                    "Timestamp": self.preloader.timestamps[t],
                    "ViolationFound": len(data[t]) > 3,
                    "Boxes": res
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

        object_results = copy.deepcopy(await self.preloader.obj_img_base[timestamp].get_clustered_boxes())
        text_results = copy.deepcopy(await self.preloader.text_img_base[timestamp].get_clustered_boxes())

        txt_removals = []
        obj_removals = []
        object_polygons = get_object_polygons(object_results)
        for r in text_results:
            tp = Polygon([(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])  # text polygon
            for op in object_polygons:
                intersection = tp.intersection(op[1])
                # Remove frame objects (text/image) if they do intersect much
                # and thus the smaller object does not impact much on cluster formation
                if intersection \
                        and (intersection.area > tp.area * 0.8 or intersection.area > op[1].area * 0.8):
                    if op[1].area > tp.area:
                        txt_removals.append(r)
                    else:
                        obj_removals.append(op[0])
        for r in txt_removals:
            text_results.remove(r)
        for r in obj_removals:
            object_results.remove(r)
        result = text_results
        result.extend(object_results)
        results = []
        for r in result:
            results.append({
                    "BoundingBox": {
                        "Left": r[0],
                        "Top": r[1],
                        "Width": r[2] - r[0],
                        "Height": r[3] - r[1]
                    }
                })
        return results


def get_object_polygons(object_result_boxes):
    object_polygons = []
    for o in object_result_boxes:
        object_polygons.append([
            o,
            Polygon([(o[0], o[1]), (o[2], o[1]), (o[2], o[3]), (o[0], o[3])])
        ])  # result obj polygon
    return object_polygons
