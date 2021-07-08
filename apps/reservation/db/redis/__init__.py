"""
Base redis session object for chat of telegrambot.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

import logging
import redis

from config import CONFIG

LOGGER = logging.getLogger(__name__)
REDIS_CONF = CONFIG['DB']['redis']


def _create_redis_object():
    try:
        host = REDIS_CONF['host']
        port = REDIS_CONF['port']
    except KeyError as ke:
        LOGGER.critical(f'Redis config missing, {ke}')
        raise

    conn = redis.StrictRedis(
        host=host,
        port=port,
        charset='utf-8',
        decode_responses=True,
    )

    return conn


REDIS = _create_redis_object()
