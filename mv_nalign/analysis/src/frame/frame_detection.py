import numpy as np


class Frame:

    def _frame_detection(self):
        pass

    async def get_aws_boxes(self) -> list:
        pass

    async def get_points(self) -> np.array:
        pass

    async def get_clustered_points(self) -> np.array:
        pass

    async def get_clustered_boxes(self) -> list:
        pass
