import asyncio
import cv2
from mv_nalign.analysis.src.data_preloader import PreLoader


class Principle:
    def __init__(self, preloader: PreLoader):
        self.preloader = preloader

    def run(self):
        pass

    # If bucket is none, function searches for file locally
    def img_run_detection(self) -> dict:
        """
        :param file:
        :param bucket:
        :return:
        """
        results = asyncio.run(self._frame_detection())
        return results

    # If bucket is none, function searches for file locally
    def video_run_detection(self) -> list:
        """
        If bucket is none, function searches for file locally
        :param file:
        :param bucket:
        :return: tuple
        """
        return asyncio.run(self._frame_series_detection())

    async def _frame_detection(self, timestamp=0):
        """
        :param frame:
        :return:
        """
        pass

    async def _frame_series_detection(self):
        """
        Method for video frames processing
        :param cap: Numpy array. Capture got from cv2.
        :return: tuple
        """
        frame_requests = []
        for timestamp in self.preloader.timestamps:
            frame_requests.append(self._frame_detection(timestamp))
        result = await asyncio.gather(*frame_requests)
        return result

