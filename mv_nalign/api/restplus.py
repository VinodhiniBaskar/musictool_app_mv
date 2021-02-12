import logging
import traceback
import os
from flask_restplus import Api
from mv_nalign import settings
from flask import url_for

log = logging.getLogger(__name__)

api = Api(version='1.0', title='Neuro Tool',
          description='One API to bind them and Databases to rule them all')


@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    if not settings.FLASK_DEBUG:
        return {'status':'FAIL', 'message': message}, 500
# def handle_mvexception(error):
#
#    response = error.to_dict()
#    print("fdf==",response)
#    return response, error.status_code


class ReverseProxied(object):

    """ This class defines the handling reverse proxy behind nginx for solving url prefix """

    
    def __init__(self, app):
        log.debug("reverse proxy class executed")
        self.app = app 

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_FORWARDED_PROTO', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme

        log.debug("wsgi returning here")
        return self.app(environ, start_response)