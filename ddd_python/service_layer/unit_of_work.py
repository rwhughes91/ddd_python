from abc import ABC, abstractmethod

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ddd_python import config
from ddd_python.adapters import repository

from .messagebus import MessageBus


class AbstractUnitOfWork(ABC):
    products: repository.AbstractProductRepository
    messagebus: MessageBus

    def __init__(self, messagebus: MessageBus):
        self.messagebus = messagebus

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @abstractmethod
    def rollback(self):
        raise NotImplementedError

    @abstractmethod
    def _commit(self):
        raise NotImplementedError

    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                event = product.events.pop(0)
                self.messagebus.handle(event)

    def commit(self):
        self._commit()
        self.publish_events()


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self, messagebus: MessageBus):
        super().__init__(messagebus)
        self.products = repository.FakeProductRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(config.postgres_uri, isolation_level="REPEATABLE READ")
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, messagebus: MessageBus, session_factory=DEFAULT_SESSION_FACTORY):
        super().__init__(messagebus)
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.products = repository.SqlAlchemyProductRepository(self.session)

    def __exit__(self, *args):
        self.session.close()

    def _commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
