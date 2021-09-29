from abc import ABC, abstractmethod

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ddd_python import config
from ddd_python.adapters import repository
from ddd_python.adapters.email import AbstractEmailAdapter


class AbstractUnitOfWork(ABC):
    products: repository.AbstractProductRepository
    email: AbstractEmailAdapter

    def __init__(self, email: AbstractEmailAdapter):
        self.email = email

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

    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                # we return an iterator because much easier than returning an iterable
                # all iterators are iterables
                # not all iterables are iterators
                yield product.events.pop(0)


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self, email: AbstractEmailAdapter):
        super().__init__(email)
        self.products = repository.FakeProductRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(config.postgres_uri, isolation_level="REPEATABLE READ")
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self, email: AbstractEmailAdapter, session_factory=DEFAULT_SESSION_FACTORY
    ):
        super().__init__(email)
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
