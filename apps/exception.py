"""
Namu's custom exception classes.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""


class NamuApiException(Exception):
    code = 500
    response = 'Internal Server Error.'
    args: tuple = ()
    kwargs: dict = {}

    def __init__(self, response: str = None, *args, **kwargs):
        if response is not None:
            self.response = response
        self.args = (*self.args, *args)
        self.kwargs = {**self.kwargs, **kwargs}
        super().__init__(self.response, *self.args, *self.kwargs.items())


class ClientError(NamuApiException):
    code = 400
    response = 'Bad request.'


class NotFoundError(ClientError):
    code = 404
    response = 'Resource does not exist.'


class DetailedNotFoundError(NotFoundError):
    resource_name: str = 'Default Resource'

    def __init__(self, filter_: dict, *args, **kwargs):
        super().__init__(f'{self.resource_name} not found by {filter_!r}', *args, **kwargs)
