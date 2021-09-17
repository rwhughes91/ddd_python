from datetime import date
from typing import Dict, List

from ddd_python.domain import model

from . import errors, unit_of_work


def allocate(
    orderid: str,
    sku: str,
    qty: int,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = model.OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise errors.InvalidSku(f"Invalid sku {line.sku}")
        batch_ref = model.allocate(line, batches)
        uow.commit()
        return batch_ref


def list_batches(uow: unit_of_work.AbstractUnitOfWork) -> List[Dict[str, object]]:
    with uow:
        batches = [
            {"ref": batch.reference, "eta": batch.eta} for batch in uow.batches.list()
        ]
        return batches


def add_batch(
    ref: str, sku: str, qty: int, eta: date, uow: unit_of_work.AbstractUnitOfWork
) -> str:
    with uow:
        batch = model.Batch(ref, sku, qty, eta)
        uow.batches.add(batch)
        uow.commit()
        return batch.reference


def edit_batch(ref: str, eta: date, uow: unit_of_work.AbstractUnitOfWork) -> str:
    with uow:
        batch = uow.batches.get(ref)
        batch.eta = eta
        uow.commit()
        return batch.reference


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}
