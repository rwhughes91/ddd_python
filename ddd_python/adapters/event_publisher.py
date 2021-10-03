import json
from abc import ABC, abstractmethod
from dataclasses import asdict

from redis import Redis

from ddd_python.domain import events


class AbstractPublisherAdapter(ABC):
    @abstractmethod
    def publish(self, channel: str, event: events.Event):
        raise NotImplementedError


class FakePublisherAdapter(AbstractPublisherAdapter):
    def publish(self, channel: str, event: events.Event):
        raise NotImplementedError


class RedisPublisherAdapter(AbstractPublisherAdapter):
    def __init__(self, host: str, port: int):
        self.r = Redis(
            host=host,
            port=port,
        )

    def publish(self, channel: str, event: events.Event):
        self.r.publish(channel, json.dumps(asdict(event)))
