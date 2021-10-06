from abc import ABC, abstractmethod
from typing import Dict, List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ddd_python import config
from ddd_python.adapters import repository
from ddd_python.adapters.email import AbstractEmailAdapter
from ddd_python.adapters.event_publisher import AbstractPublisherAdapter


class AbstractUnitOfWork(ABC):
    products: repository.AbstractProductRepository
    email: AbstractEmailAdapter
    event_publisher: AbstractPublisherAdapter

    def __init__(
        self, email: AbstractEmailAdapter, event_publisher: AbstractPublisherAdapter
    ):
        self.email = email
        self.event_publisher = event_publisher

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @abstractmethod
    def rollback(self):
        raise NotImplementedError

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def execute(self, query: str, payload: Dict[str, str]):
        raise NotImplementedError

    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                # we return an iterator because much easier than returning an iterable
                # all iterators are iterables
                # not all iterables are iterators
                yield product.events.pop(0)


class FakeUnitOfWork(AbstractUnitOfWork):
    queries: List[str]

    def __init__(
        self, email: AbstractEmailAdapter, event_publisher: AbstractPublisherAdapter
    ):
        super().__init__(email, event_publisher)
        self.products = repository.FakeProductRepository([])
        self.committed = False
        self.queries = []

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def execute(self, query: str, payload: Dict[str, str]):
        self.queries.append(query)


DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(config.postgres_uri, isolation_level="REPEATABLE READ")
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        email: AbstractEmailAdapter,
        event_publisher: AbstractPublisherAdapter,
        session_factory=DEFAULT_SESSION_FACTORY,
    ):
        super().__init__(email, event_publisher)
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.products = repository.SqlAlchemyProductRepository(self.session)

    def __exit__(self, *args):
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def execute(self, query: str, payload: Dict[str, str]):
        return self.session.execute(query)
