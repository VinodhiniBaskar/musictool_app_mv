import os
import cv2
from pathlib import Path
# import dotenv
##bootstrap is added
VERSION = 1

# init configuration
root_dir = os.path.dirname(os.path.abspath(__file__))
# dotenv.load_dotenv(dotenv_path=root_dir+'/.env')


def path(rel):
    return os.path.join(root_dir, rel.lstrip('/'))


def tmp(rel):
    tmp_dir = Path(path('var/tmp'))
    tmp_dir.mkdir(parents=True, exist_ok=True)

    return str(tmp_dir/rel)


GAZE_ARCH = os.getenv('GAZE_ARCH') or 'v2'
GAZE_MODEL = os.getenv('GAZE_MODEL') or 'weights.h5'
