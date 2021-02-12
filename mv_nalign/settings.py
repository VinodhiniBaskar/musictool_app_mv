# Flask settings
# FLASK_SERVER_NAME = 'localhost:8888'

GUNICORN_ENABLE = False
FLASK_DEBUG = True  # Do not use debug mode in production
# Flask-Restplus settings
RESTPLUS_SWAGGER_UI_DOC_EXPANSION = 'list'
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = False
RESTPLUS_ERROR_404_HELP = False

MV_DATABASE_NAME = 'nalign'
MONGO_SERVER_NAME = 'mongodb://192.168.1.50'
DEFAULT_USER_ID_CUSTOM = "mv_user"
DEFAULT_USER_ID_SYSTEM = "mv_system"
BASE_URL_PREFIX='/api/v1/'


HOST = '0.0.0.0'
MONGO_SERVER_NAME = 'mongodb://localhost'
MVSERVICE_SERVER_NAME = 'http://0.0.0.0'
MVSERVICE_EXT_SERVER_NAME = 'http://10.10.10.62'
DEMOGRAPHIC_PORT = 8000
BRAND_PORT = 8002
SPARK_PORT = 8003
CPC_PORT = 8004
STUDY_PORT = 8005
PROJECT_PORT = 8006
METAPHOR_INPUT_PORT = 8020
NALIGN_PORT = 7003
# CLIENT_SECRETS_FILE = "client_secret_1007468633005-8a5efadon2tp5pcdk3q2pl2l62ml1bf7.apps.googleusercontent.com.json"
CLIENT_SECRETS_FILE = "client_secret_107162302051-k7f9rdunspmjdvr0mb24dfusge1g1tm2.apps.googleusercontent.com.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
MAX_IMAGE_FILE_SIZE = 16777216
BASE_MEDIA_PATH = "mv_nalign/media/"
MEDIA_PATH="/media"
ROLE_ARN = 'arn:aws:iam::274822417273:role/AmazonRekognitionServiceRoleCopy'
VIDEO_BUCKET_NAME = 'machine-vantage-inc-video'
IMAGE_BUCKET_NAME = "machine-vantage-inc-images"
# # #Production
# # # nalign_PORT = 7001
# GUNICORN_ENABLE = True	
# FLASK_DEBUG = False  # Do not use debug mode in production

