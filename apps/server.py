"""
WSGI entrypoint.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

from apps import create_app


app = create_app()
