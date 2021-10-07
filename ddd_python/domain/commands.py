from dataclasses import dataclass
from datetime import date


class Command:
    pass


@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int


@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: date


@dataclass
class ChangeBatchQuantity(Command):
    ref: str
    qty: int


@dataclass
class GetProducts(Command):
    pass


@dataclass
class CreateProduct(Command):
    sku: str


@dataclass
class GetBatches(Command):
    sku: str


@dataclass
class Deallocate(Command):
    ref: str
    orderid: str
    sku: str
    qty: int
