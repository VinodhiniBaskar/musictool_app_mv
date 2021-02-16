import logging.config
import logging
from flask import Flask, Blueprint
from flask_cors import CORS
import os
from mv_nalign import settings
from mv_nalign.api.naligns.endpoints.nalign import ns as nalign_namespace
from mv_nalign.api.restplus import api,ReverseProxied
from mv_nalign.mvexception.exception import register_error_handlers
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.contrib.fixers import ProxyFix
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' 
app = Flask(__name__)
#app = Flask(__name__, static_url_path='/static', static_folder="/DATA/PROJECTS/musiq_app/musictool_app_mv/mv_nalign/static")

app.wsgi_app = ProxyFix(app.wsgi_app)
# UPLOAD_FOLDER = 'mv_nalign/media'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"*": {"origins": "*"}})
logging.config.fileConfig('logging.conf')


if settings.GUNICORN_ENABLE:
    app.wsgi_app = ReverseProxied(app.wsgi_app) #when server http proxy
    gunicorn_error_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers.extend(gunicorn_error_logger.handlers)

log = logging.getLogger(__name__)

def configure_app(flask_app):

    # change to mongo db
    flask_app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
    flask_app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
    flask_app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
    flask_app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP
    

        
def initialize_app(flask_app):

    configure_app(flask_app)

    blueprint = Blueprint('api', __name__, url_prefix='/api/v1',static_folder='')
    api.init_app(blueprint)
    api.add_namespace(nalign_namespace)
    flask_app.register_blueprint(blueprint)
    register_error_handlers(api, flask_app, settings.FLASK_DEBUG)

def main():    
    log.info('>>>>> Starting development server at http://{}/api/v1 <<<<<'.format(app.config['SERVER_NAME']))
    initialize_app(app)
    app.run(debug=settings.FLASK_DEBUG, host=settings.HOST, port=settings.NALIGN_PORT)#,ssl_context=('cert.pem', 'key.pem'))

if settings.GUNICORN_ENABLE :
    initialize_app(app)

if __name__ == "__main__":
    main()
            
