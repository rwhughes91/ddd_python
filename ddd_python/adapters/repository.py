from abc import ABC, abstractmethod
from typing import List, Set

from sqlalchemy.orm import Session

from ddd_python.domain import model


class AbstractProductRepository(ABC):
    @abstractmethod
    def add(self, batch: model.Product):
        raise NotImplementedError

    @abstractmethod
    def get(self, sku: str) -> model.Product:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> List[model.Product]:
        raise NotImplementedError


class FakeProductRepository(AbstractProductRepository):
    _products: Set[model.Product]

    def __init__(self, products: List[model.Product]):
        self._products = set(products)

    def add(self, product: model.Product):
        self._products.add(product)

    def get(self, sku: str):
        return next(p for p in self._products if p.sku == sku)

    def list(self):
        return list(self._products)


class SqlAlchemyProductRepository(AbstractProductRepository):
    session: Session

    def __init__(self, session: Session):
        self.session = session

    def add(self, product: model.Product) -> None:
        self.session.add(product)

    def get(self, sku: str) -> model.Product:
        return self.session.query(model.Product).filter_by(sku=sku).one()

    def list(self) -> List[model.Product]:
        return self.session.query(model.Product).all()
