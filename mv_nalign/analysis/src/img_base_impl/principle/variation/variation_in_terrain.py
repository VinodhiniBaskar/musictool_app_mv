import numpy as np
from mv_nalign.analysis.src.common import fill_gaps
import cv2
import asyncio
from mv_nalign.analysis.src.img_base_impl.principle.principle import Principle
from mv_nalign.analysis.src.segmentation.body_segmentator import create_body_segmentator


class VariationInTerrainPrinciple(Principle):

    def run(self):
        data = self.video_run_detection()

        return {
            "VideoResolution": {"Width": self.preloader.width, "Height": self.preloader.height},
            "ViolationFound": bool(len(data)),
            "Results": data
        }

    # If bucket is none, function searches for file locally
    def video_run_detection(self) -> tuple:
        """
        If bucket is none, function searches for file locally
        :param file:
        :param bucket:
        :return: tuple
        """
        cap = cv2.VideoCapture(self.preloader.public_aws_path)
        delimiter_timestamps = self.detect_scene_changes(cap, create_body_segmentator())
        timestamps = asyncio.run(self._frame_series_detection(delimiter_timestamps))
        return timestamps

    async def _frame_series_detection(self, delimiter_timestamps):
        """
        Method for video frames processing
        :param cap: Numpy array. Capture got from cv2.
        :return: tuple
        """
        timestamps = []
        for dt in delimiter_timestamps:
            if not dt:
                continue

            left_frame_timestamp = int(dt - self.preloader.time_step)
            right_frame_timestamp = int(dt + self.preloader.time_step)
            if (left_frame_timestamp in self.preloader.timestamps) and (right_frame_timestamp in self.preloader.timestamps):
                faces_on_the_left = await self.preloader.face_img_base[left_frame_timestamp].get_aws_boxes()
                faces_on_the_right = await self.preloader.face_img_base[right_frame_timestamp].get_aws_boxes()
                if len(faces_on_the_left) and len(faces_on_the_right):
                    timestamps.append(int(dt))

        return timestamps

    def detect_scene_changes(self, video, segmentator, threshold=0.33, kernel=3, bins=16):
        """
        Detect timestamps when the scene changes
        :param video: result of VideoCapture
        :param segmentator: BodyPix segmentator (BodySegmentator class)
        :param threshold: The threshold value of the histogram change from 0 to 1,
            values above which are interpreted as a scene change
        :param time_delta: spacing between frames for histogram matching in milliseconds
        :param kernel: Distance between frames for which the difference of histograms is calculated
        :param bins: number of histogram bins
        :return:
        """
        frames = 0
        timestamp = 0
        fps = video.get(cv2.CAP_PROP_FPS)
        histograms = []
        timestamps = []

        # calculation of histograms
        while True:
            frame_num = int(timestamp * fps / 1000)
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = video.read()
            if frame is None:
                break
            frames += 1
            timestamp += self.preloader.time_step
            timestamps.append(timestamp)
            body_contour = segmentator.get_body(frame)
            # Draw the rectangle around each face
            cv2.drawContours(frame, body_contour, -1, (0, 0, 0), -1)
            min_value = 255 // bins
            histograms.append(
                cv2.calcHist([frame], [0, 1, 2], None, [bins, bins, bins],
                             [min_value, 255, min_value, 255, min_value, 255])
            )

        timestamps = np.array(timestamps)

        # hist similarity
        similarity = np.full(frames, np.nan)
        for i in range(frames - 1):
            similarity[i] = cv2.compareHist(histograms[i], histograms[i + 1], 4)
        similarity[-1] = 0

        # moving average
        conv = np.ones(kernel) / kernel
        trend = np.convolve(similarity, conv, mode="same")
        trend = fill_gaps(trend)

        # calculate difference
        difference = similarity - trend
        difference[difference < 0] = 0

        # scenes changes detection
        med = np.max(difference) * threshold
        mask = difference >= med
        need_face = mask.copy()
        need_face[1: frames] = np.bitwise_or(need_face[1: frames], need_face[0: frames - 1])

        return timestamps[mask]

