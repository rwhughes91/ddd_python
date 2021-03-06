from dataclasses import dataclass
from datetime import date
from typing import List, Union

from . import commands, events

Events = List[Union[commands.Command, events.Event]]


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
    allocations: List[OrderLine]
    _purchased_quantity: int

    def __init__(self, ref: str, sku: str, qty: int, eta: date) -> None:
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self.allocations = []

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

    @property  # no setter means any setting will raise Exception
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self.allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    @property
    def has_allocations(self) -> bool:
        if len(self.allocations):
            return True
        return False

    def add_allocation(self, line: OrderLine):
        allocations = set(self.allocations)
        allocations.add(line)

        self.allocations = list(allocations)

    def remove_allocation(self, line: OrderLine):
        allocations = set(self.allocations)
        allocations.remove(line)

        self.allocations = list(allocations)

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self.add_allocation(line)

    def deallocate(self, line: OrderLine) -> None:
        if line in self.allocations:
            self.remove_allocation(line)

    def deallocate_one(self) -> OrderLine:
        return self.allocations.pop()


# Aggregates
class Product:
    sku: str
    batches: List[Batch]
    version_number: int
    events: Events

    def __new__(cls, *args, **kwargs):
        instance = super(Product, cls).__new__(cls)
        instance.events = []
        return instance

    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        # this will not be called when ORM is mapped
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events.append(events.ProductCreated(sku))

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
            self.events.append(
                events.Allocated(
                    orderid=line.orderid,
                    sku=line.sku,
                    qty=line.qty,
                    batchref=batch.reference,
                )
            )
            self.version_number += 1
            return batch.reference
        except StopIteration:
            self.events.append(events.OutOfStock(self.sku))

    def deallocate(self, ref: str, line: OrderLine):
        batch = next(b for b in self.batches if b.reference == ref)
        batch.deallocate(line)
        self.version_number += 1
        self.events.append(events.Deallocated(orderid=line.orderid, sku=line.sku))

    def add_batches(self, batches: List[Batch]):
        today = date.today()
        current_batches = set(self.batches)
        for batch in batches:
            if batch.sku != self.sku:
                raise InvalidSku(f"{batch.sku} does not match {self.sku}")
            if batch.eta < today:
                raise InvalidETA("ETA cannot be in the past")
            current_batches.add(batch)
        self.batches = list(current_batches)
        self.events.extend(
            events.BatchCreated(
                sku=batch.sku,
                reference=batch.reference,
                eta=batch.eta,
                qty=batch._purchased_quantity,
            )
            for batch in batches
        )
        self.version_number += 1
        return [batch for batch in self.batches if not batch.has_allocations]

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(b for b in self.batches if b.reference == ref)
        batch._purchased_quantity = qty
        self.events.append(events.BatchQuantityChanged(ref=ref, qty=qty))
        self.version_number += 1
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(events.Deallocated(orderid=line.orderid, sku=line.sku))
            self.events.append(commands.Allocate(line.orderid, line.sku, line.qty))
