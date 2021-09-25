from abc import ABC, abstractmethod

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ddd_python import config
from ddd_python.adapters import repository


class AbstractUnitOfWork(ABC):
    products: repository.AbstractProductRepository

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
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
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
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
