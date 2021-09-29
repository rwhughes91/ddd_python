from abc import ABC, abstractmethod
from typing import List, Set

from sqlalchemy.orm import Session

from ddd_python.domain import model

from . import orm


class AbstractProductRepository(ABC):
    seen: Set[model.Product]

    def __init__(self):
        self.seen = set()

    def add(self, product: model.Product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku: str) -> model.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batchref(self, batchref) -> model.Product:
        product = self._get_by_batchref(batchref)
        if product:
            self.seen.add(product)
        return product

    @abstractmethod
    def _add(self, product: model.Product):
        raise NotImplementedError

    @abstractmethod
    def _get(self, sku: str) -> model.Product:
        raise NotImplementedError

    @abstractmethod
    def _get_by_batchref(self, batchref) -> model.Product:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> List[model.Product]:
        raise NotImplementedError


class FakeProductRepository(AbstractProductRepository):
    _products: Set[model.Product]

    def __init__(self, products: List[model.Product]):
        super().__init__()
        self._products = set(products)

    def _add(self, product: model.Product):
        self._products.add(product)

    def _get(self, sku: str):
        return next(p for p in self._products if p.sku == sku)

    def _get_by_batchref(self, batchref):
        return next(
            (p for p in self._products for b in p.batches if b.reference == batchref),
            None,
        )

    def list(self):
        return list(self._products)


class SqlAlchemyProductRepository(AbstractProductRepository):
    session: Session

    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def _add(self, product: model.Product) -> None:
        self.session.add(product)

    def _get(self, sku: str) -> model.Product:
        return self.session.query(model.Product).filter_by(sku=sku).one()

    def _get_by_batchref(self, batchref):
        return (
            self.session.query(model.Product)
            .join(model.Batch)
            .filter(orm.batches.c.reference == batchref)
            .first()
        )

    def list(self) -> List[model.Product]:
        return self.session.query(model.Product).all()
