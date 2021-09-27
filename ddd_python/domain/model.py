from dataclasses import dataclass
from datetime import date
from typing import List, Set

from . import events


class OutOfStock(Exception):
    pass


class InvalidETA(Exception):
    pass


class InvalidSku(Exception):
    pass


# unsafe hash must be used because sqlalchemy edits dataclass
@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    reference: str
    sku: str
    eta: date
    _purchased_quantity: int
    _allocations: Set[OrderLine]

    def __init__(self, ref: str, sku: str, qty: int, eta: date) -> None:
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()  # type Set[Orderline]

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __lt__(self, other):
        if self.eta is None:
            return True
        if other.eta is None:
            return False
        return self.eta < other.eta

    @property
    def order_allocations(self) -> List[OrderLine]:
        return [*self._allocations]

    @property  # no setter means any setting will raise Exception
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    @property
    def has_allocations(self) -> bool:
        if len(self.order_allocations):
            return True
        return False

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)


# Aggregates
class Product:
    sku: str
    batches: List[Batch]
    version_number: int
    events: List[events.Event]

    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events = []

    def __eq__(self, other):
        if not isinstance(other, Product):
            return False
        return other.sku == self.sku

    def __hash__(self):
        return hash(self.sku)

    def allocate(self, line: OrderLine):
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            return batch.reference
        except StopIteration:
            self.events.append(events.OutOfStock(self.sku))

    def order_batches(self, batches: List[Batch]):
        today = date.today()
        current_batches = set(self.batches)
        for batch in batches:
            if batch.sku != self.sku:
                raise InvalidSku(f"{batch.sku} does not match {self.sku}")
            if batch.eta < today:
                raise InvalidETA("ETA cannot be in the past")
            current_batches.add(batch)
        self.batches = list(current_batches)
        self.version_number += 1
        return [batch for batch in self.batches if not batch.has_allocations]
