import traceback
from werkzeug.wsgi import ClosingIterator

from flask import Flask


class AfterThisResponse:
    def __init__(self, app: Flask = None):
        self.callbacks = []
        if app:
            self.init_app(app)

    def __call__(self, callback):
        self.callbacks.append(callback)
        return callback

    def init_app(self, app: Flask):
        # Install extension
        app.after_this_response = self

        # Install middleware
        app.wsgi_app = AfterThisResponseMiddleware(app.wsgi_app, self)

    def flush(self):
        try:
            for fn in self.callbacks:
                try:
                    fn()
                except Exception:
                    traceback.print_exc()
        finally:
            self.callbacks = []


class AfterThisResponseMiddleware:
    def __init__(self, application: Flask, after_this_response_ext: AfterThisResponse):
        self.application = application
        self.after_this_response_ext = after_this_response_ext

    def __call__(self, environ, start_response):
        iterator = self.application(environ, start_response)
        try:
            return ClosingIterator(iterator, [self.after_this_response_ext.flush])
        except Exception:
            traceback.print_exc()
            return iterator
