"""
Redis session object for chat.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

from datetime import timedelta

from apps.reservation.db.redis import REDIS


TTL = timedelta(seconds=1800)


class ChatSession:
    def __init__(self, chat_id: str):
        # TODO: Add selenium object variable to redis session
        self.name = f'chat_session_{chat_id}'
        data = REDIS.hgetall(self.name)
        self.username = data.get('username')

    def exists(self):
        return bool(REDIS.exists(self.name))

    def commit(self):
        """Update current data to redis server"""
        REDIS.hmset(
            name=self.name,
            mapping={
                'username': self.username,
                # TODO: Add selenium object variable
            },
        )
        self.touch()

    def touch(self):
        """Reset TTL"""
        REDIS.expire(self.name, TTL)

    def delete(self):
        """Delete session"""
        REDIS.delete(self.name)
