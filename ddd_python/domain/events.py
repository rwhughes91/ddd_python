from dataclasses import dataclass
from datetime import date


class Event:
    pass


@dataclass
class OutOfStock(Event):
    sku: str


@dataclass
class Allocated(Event):
    orderid: str
    sku: str
    qty: int
    batchref: str


@dataclass
class Deallocated(Event):
    orderid: str
    sku: str


@dataclass
class ProductCreated(Event):
    sku: str


@dataclass
class BatchCreated(Event):
    sku: str
    reference: str
    eta: date
