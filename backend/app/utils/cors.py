from functools import wraps

from flask import make_response
from flask import request


def cors_preflight():
    def wrapper(fn):
        @wraps(fn)
        def decorated_function(*args, **kwargs):
            if request.method == 'OPTIONS':
                response = make_response()
                response.headers.add('Access-Control-Allow-Origin', 'http://localhost:328')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
                response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response
            return fn(*args, **kwargs)

        return decorated_function

    return wrapper
