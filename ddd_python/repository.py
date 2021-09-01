from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from .models import Batch


class AbstractRepository(ABC):
    @abstractmethod
    def add(self, batch: Batch):
        raise NotImplementedError

    @abstractmethod
    def get(self, reference) -> Batch:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> Batch:
        raise NotImplementedError


class FakeRepository(AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list_all(self):
        return list(self._batches)


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(Batch).filter_by(reference=reference).one()

    def list_all(self):
        return self.session.query(Batch).all()
