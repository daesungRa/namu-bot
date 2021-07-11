"""
Redis session object for chat.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

import logging
from datetime import timedelta
from typing import Dict, Optional

from apps.reservation.db.redis import REDIS
from config import CONFIG


LOGGER = logging.getLogger(__name__)
REDIS_CONF = CONFIG['DB']['redis']
TTL = timedelta(seconds=REDIS_CONF['ttl'])


class ChatSession:
    name: Optional[str] = None
    chat_id: Optional[str] = None
    username: Optional[str] = None
    kwargs: Optional[Dict] = None

    def __init__(self, chat_id: str):
        """Set and Get redis session info."""
        if chat_id is None:
            raise ValueError(f'[REDIS] No chat_id inserted.')

        self.name = f'chat_session_{chat_id}'
        self.chat_id = chat_id

        session_info = REDIS.hgetall(self.name)
        if 'username' in session_info:
            self.username = session_info.pop('username')
            self.kwargs = {**session_info}

    def exists(self):
        return bool(REDIS.exists(self.name))

    def commit(self, **kwargs):
        """Update current data to redis server"""
        assert self.username is not None

        REDIS.hmset(
            name=self.name,
            mapping={
                'chat_id': self.chat_id,
                'username': self.username,
                **kwargs,
            },
        )
        self.touch()
        LOGGER.info(f"[REDIS] {self.name} Updated.")

    def touch(self):
        """Reset TTL"""
        REDIS.expire(self.name, TTL)

    def delete(self):
        """Delete session"""
        REDIS.delete(self.name)
        LOGGER.info(f"[REDIS] {self.name} Deleted..")
