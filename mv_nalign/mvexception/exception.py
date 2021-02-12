# -*- coding: utf-8 -*-
from mv_nalign.api.restplus import api
import re
from flask import jsonify

class Test():
    def __init__(self, message):
        print(message)

    def add(self,x,y):
        print('exception page')
        return x+y
class MVException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def out_val(self, dit):
        for key, value in dit.items():
            if isinstance(value, list):
                return key, value[0]
            else:
                return self.out_val(value)

    def to_dict(self):
        rv = dict(self.payload or ())
        if self.message is not None:
            """for loops means to validation part"""
            rv['status'] = 'FAIL'
            rv['message'] = self.message
            if type(self.message) is not str:
                rv['status'] = 'FAIL'
                output = self.out_val(self.message)
                key, value = output
                if re.match(r'^Missing',value):
                    rv['message'] = key +" is required"
                else:
                    rv['message'] = value
        return rv


@api.errorhandler(MVException)
def handle_mvexception(error):
    response = error.to_dict()
    print("qw=====", response)
    return response, error.status_code


class ValidationException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, errors={}):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.errors = errors

    def to_dict(self):
        rv = dict()
        rv['status'] = 'FAIL'
        rv['message'] = self.message
        rv['errors'] = self.errors
        return rv


@api.errorhandler(ValidationException)
def handle_validation_exception(error):
    response = error.to_dict()
    return response, error.status_code


class MVNotFoundError(MVException):
    status_code = 404
    message = 'Resource not found'

class MVBadRequestError(MVException):
    status_code = 400
    message = 'Bad Request'

class MVServerError(MVException):
    status_code = 500
    message = 'Internal Server Error'


def register_error_handlers(api, app, debug):
    # restplus handlers

    @api.errorhandler(MVException)
    def handle_mvexception(error):
        response = error.to_dict()
        response['from'] = 'rest-plus'
        return response, error.status_code

    @api.errorhandler(MVNotFoundError)
    def handle_not_found_exception(error):
        return handle_mvexception(error)

    @api.errorhandler(ValidationException)
    def handle_validation_exception(error):
        return handle_mvexception(error)

    @api.errorhandler
    def default_error_handler(e):
        message = 'An unhandled exception occurred. in rest-plus'
        # log.exception(message)

        if not debug:
            return {'status': 'FAIL', 'message': message}, 500

    # flask handlers

    @app.errorhandler(MVException)
    def handle_mvexception_flask(error):
        response = error.to_dict()
        # response['from'] = 'flask'
        return jsonify(response), error.status_code

    @app.errorhandler(MVNotFoundError)
    def handle_not_found_exception(error):
        return handle_mvexception_flask(error)

    @app.errorhandler(ValidationException)
    def handle_validation_exception(error):
        return handle_mvexception_flask(error)

    @app.errorhandler(Exception)
    def default_error_handler(e):
        message = 'An unhandled exception occurred. in flask'
        # log.exception(message)

        if not debug:
            return jsonify({'status': 'FAIL', 'message': message}), 500
