import asyncio
from mv_nalign.analysis.src.img_base_impl.principle.principle import Principle
from mv_nalign.analysis.src.common_helper import to_amazon_box, filter_by_size


class LogoPrinciple(Principle):

    def run(self):
        if self.preloader.file_type == 'img':
            raise Exception('Images are not supported by this principle')
        else:
            data = self.video_run_detection()
            return {
                "VideoResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
                "ViolationFound": bool(len(data)),
                "Results": data
            }

    async def _frame_detection(self, timestamp=0):
        """
        :param frame:
        :return:
        """
        object_results = await self.preloader.obj_img_base[timestamp].get_aws_boxes()
        text_results = await self.preloader.text_img_base[timestamp].get_clustered_boxes()
        text_results = [to_amazon_box(x) for x in text_results]
        # text_results = filter_by_size(text_results, 0.07)
        logo_results = await self.preloader.logo_img_base[timestamp].get_google_boxes()
        logo_results = filter_by_size(logo_results, 0.09)
        print(logo_results)
        persons_count = sum(x["Name"] == "Person" for x in object_results)
        results = {
            "persons_count": persons_count,
            "text_boxes_count": len(text_results),
            "logos_count": len(logo_results),
        }
        return results

    def video_run_detection(self) -> list:
        """
        If bucket is none, function searches for file locally
        :param file:
        :param bucket:
        :return: tuple
        """
        intervention_timestamps = []
        assumable_interventions = []

        wait_for_product_intervention = False
        result = asyncio.run(self._frame_series_detection())

        # post-process results
        for i in range(0, len(self.preloader.timestamps)):
            # If there are persons in current frame..
            if result[i]["persons_count"]:
                # ..but previously we caught some frames, that potentially are intervening story...
                if len(assumable_interventions):
                    # ...we accept these as intervention....
                    intervention_timestamps.extend(assumable_interventions)
                    # ....and free space for a new potential part
                    assumable_interventions = []
                # ..we mark this fact to check later, when logo or text will appear instead
                wait_for_product_intervention = True
            # If there were persons on some of the previous frames and now there is text or logo
            # we assume there there is an intervention, except case, persons will not appear anymore.
            elif wait_for_product_intervention and (result[i]["logos_count"] or result[i]["text_boxes_count"]):
                assumable_interventions.append(self.preloader.timestamps[i])
        return intervention_timestamps
