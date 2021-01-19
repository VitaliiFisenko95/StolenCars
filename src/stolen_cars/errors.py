import logging
from json import JSONDecodeError

from bson.errors import InvalidId
from flask import Response
from pymongo.errors import DuplicateKeyError
from schematics.exceptions import DataError

LOG = logging.getLogger(__name__)


class _BaseException(Exception):
    pass


class ObjectNotFound(_BaseException):
    def __init__(self, object_id):
        super().__init__(f'Not found object with id {object_id}')


class ProcedureDeserializationError(_BaseException):
    def __init__(self, _id, ex_text):
        self._id = _id
        super().__init__(f'Can not deserialize object with id {_id}. {ex_text}')


class VinDecodeError(_BaseException):
    def __init__(self, vin, msg):
        super().__init__(f'Failed to decode vin code {vin} because of {msg}')


class ForbiddenStatusError(_BaseException):
    def __init__(self, _id):
        super().__init__(f'Cannot update object {_id} in status deleted')


class MakeFetchError(_BaseException):
    def __init__(self, msg):
        super().__init__(f'Failed to fetch makes because of {msg}')


class ModelFetchError(_BaseException):
    def __init__(self, msg):
        super().__init__(f'Failed to fetch models because of {msg}')


ERROR_DICT = {
    InvalidId: (422, '{}'),
    ObjectNotFound: (404, '{}'),
    JSONDecodeError: (422, 'Invalid json data. {}'),
    VinDecodeError: (400, '{}'),
    DuplicateKeyError: (400, '{}'),
    MakeFetchError: (404, '{}'),
    ModelFetchError: (404, '{}'),
}


class ErrorsMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)
        except DataError as ex:
            LOG.debug(ex.to_primitive())
            res = Response(ex.to_primitive(), mimetype='application/json', status=422)
            return res(environ, start_response)
        except tuple(ERROR_DICT) as ex:
            code, message = ERROR_DICT[type(ex)]
            LOG.info(message.format(ex))
            res = Response(message.format(ex), mimetype='application/json', status=code)
            return res(environ, start_response)
        except Exception as ex:
            LOG.exception(f'Unknown error caught in API - {ex}')
            res = Response('Internal server error', mimetype='application/json', status=500)
            return res(environ, start_response)
