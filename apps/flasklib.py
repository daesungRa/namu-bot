"""
Namu's custom flask library classes.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

import logging
import functools
import warnings
from typing import Type, Union, Dict, List

from flask import Flask, Blueprint, request, Response, render_template, jsonify
from flask.views import MethodView

from .exception import NamuApiException, ClientError, NotFoundError


def deprecated(func):
    """Set inserted function or method to be deprecated"""
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # Turn off filter
        warnings.warn(
            message=f"Call to deprecated function or method '{func.__name__}'.",
            category=DeprecationWarning,
            stacklevel=2
        )
        warnings.simplefilter('default', DeprecationWarning)  # Reset filter
        return func(*args, **kwargs)
    return _wrapper


class ApiView(MethodView):
    rules: Dict[str, List[str]] = {}

    @classmethod
    def register(cls, bp_or_app: Union[Flask, Blueprint]):
        view_func = cls.as_view(cls.__name__)
        for rule, methods in cls.rules.items():
            bp_or_app.add_url_rule(
                rule=rule,
                view_func=view_func,
                methods=methods,
            )


class ApiBlueprint(Blueprint):
    def __init__(self, import_name, url_prefix):
        super().__init__(
            name=import_name[import_name.find('.') + 1:],
            import_name=import_name,
            url_prefix=url_prefix,
        )

    def api_view_class(self, api_view_cls: Type[ApiView]):
        assert issubclass(api_view_cls, ApiView)
        api_view_cls.register(self)
        return api_view_cls


class NamuFlask(Flask):
    def __init__(self, app_name, logger=None):
        super().__init__(app_name)
        if logger is None:
            logger = logging.getLogger(app_name)

        @self.route('/rules')
        def get_rules():
            return jsonify(data=[
                repr(rule)
                for rule in
                sorted(self.url_map.iter_rules(), key=lambda r: r.rule)
            ])

        @self.errorhandler(NamuApiException)
        def namu_api_exception_handler(exc: NamuApiException):
            logger.error(f'{app_name!r} server caught an error')
            logger.exception(exc)
            # return jsonify({'error': repr(exc)}), 500
            return render_template(
                template_name_or_list='error/500.html',
                context={'error_message': repr(exc)}
            ), 500

        @self.errorhandler(Exception)
        def exception_handler(exc: Exception):
            logger.error(f'{app_name!r} server caught an unexpected error')
            logger.exception(exc)
            return render_template(
                template_name_or_list='error/500.html',
                context={'error_message': repr(exc)}
            ), 500

        @self.errorhandler(NotFoundError)
        def not_found_error_handler(exc: NotFoundError):
            logger.error(f'{app_name!r} Resource not found')
            logger.exception(exc)
            return render_template(
                template_name_or_list='error/404.html',
                context={'error_message': repr(exc)}
            ), 404

        @self.errorhandler(ClientError)
        def client_error_handler(exc: ClientError):
            logger.error(f'{app_name!r} wrong path or parameter')
            logger.exception(exc)
            return render_template(
                template_name_or_list='error/404.html',
                context={'error_message': repr(exc)}
            ), 400

        @self.before_request
        def logging_before_request():
            logger.info(f'> {request.method} {request.path}')

        @self.after_request
        def logging_after_request(response: Response):
            logger.info(f'< {request.method} {request.path} {response.status_code}')
            return response
