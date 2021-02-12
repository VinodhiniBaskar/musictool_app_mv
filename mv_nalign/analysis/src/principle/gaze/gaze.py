import asyncio
import mv_nalign.analysis.src.principle.gaze.analyzer as ga
from mv_nalign.analysis.src.principle.gaze.analyzer import GazeResult
from mv_nalign.analysis.src.principle.gaze.cnn import create_detector
from mv_nalign.analysis.src.principle.gaze.provider import AwsImageFacesProvider, AwsVideoFacesProvider


class Gaze:
    def __init__(self, preloader):
        self.preloader = preloader
        self.detector = create_detector()

    def run(self):
        if self.preloader.file_type == 'img':
            faces_provider = AwsImageFacesProvider(self.preloader)
        else:
            faces_provider = AwsVideoFacesProvider(self.preloader)
        analyzer = ga.Analyzer(self.detector)

        return asyncio.run(self.get_analyzer_result(analyzer, faces_provider))

    async def get_analyzer_result(self, analyzer, faces_provider):
        gaze_ts = await analyzer.get_gaze_results(faces_provider)
        result = []
        result_group = None
        for i in range(gaze_ts.shape[0]):
            if result_group is None or result_group['Timestamp'] != gaze_ts[i][GazeResult.timestamp]:
                if result_group is not None:
                    result.append(result_group)

                result_group = {
                    'Timestamp': int(gaze_ts[i][GazeResult.timestamp]),
                    'ViolationFound': False,
                    'Boxes': []
                }

            box = {
                "BoundingBox": {
                    "Left": gaze_ts[i][GazeResult.fb_x1] / gaze_ts[i][GazeResult.w],
                    "Top": gaze_ts[i][GazeResult.fb_y1] / gaze_ts[i][GazeResult.h],
                    "Width": (gaze_ts[i][GazeResult.fb_x2] - gaze_ts[i][GazeResult.fb_x1]) / gaze_ts[i][GazeResult.w],
                    "Height": (gaze_ts[i][GazeResult.fb_y2] - gaze_ts[i][GazeResult.fb_y1]) / gaze_ts[i][GazeResult.h],
                }
            }

            result_group['ViolationFound'] = result_group['ViolationFound'] or not gaze_ts[i][GazeResult.gaze_decision]
            result_group['Boxes'].append(box)

        result.append(result_group)

        source_type = faces_provider.get_type()
        if source_type == 'video':
            shape_key = 'VideoResolution'
        elif source_type == 'image':
            shape_key = 'ImageResolution'
        else:
            raise Exception('Unknown gaze source type: "%s"' % source_type)

        return {
            shape_key: {"Width": self.preloader.width, "Height": self.preloader.height},
            'Results': result
        }
