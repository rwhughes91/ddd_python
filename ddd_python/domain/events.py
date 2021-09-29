from dataclasses import dataclass
from datetime import date


class Event:
    pass


@dataclass
class AllocationRequired(Event):
    orderid: str
    sku: str
    qty: int


@dataclass
class ProductsRequired(Event):
    pass


@dataclass
class ProductCreated(Event):
    sku: str


@dataclass
class BatchesRequired(Event):
    sku: str


@dataclass
class BatchCreated(Event):
    ref: str
    sku: str
    qty: int
    eta: date


@dataclass
class BatchEdited(BatchCreated):
    pass


@dataclass
class OutOfStock(Event):
    sku: str
