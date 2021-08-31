from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Set


# unsafe hash must be used because sqlalchemy edits dataclass
@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    reference: str
    sku: str
    eta: Optional[date]
    _purchased_quantity: int
    _allocations: Set[OrderLine]

    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]) -> None:
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()  # type Set[Orderline]

    @property  # no setter means any setting will raise Exception
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property  # no setter means any setting will raise Exception
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)

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


class OutOfStock(Exception):
    pass


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")
