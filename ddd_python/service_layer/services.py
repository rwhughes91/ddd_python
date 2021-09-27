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
        product = uow.products.get(sku)
        if product:
            batch_ref = product.allocate(line)
            uow.commit()
            return batch_ref
        raise errors.InvalidSku(f"Invalid sku {sku}")


def list_products(uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        products = uow.products.list()
        return [{"sku": product.sku} for product in products]


def add_product(sku: str, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = model.Product(sku, [])
        uow.products.add(product)
        uow.commit()
        return product.sku


def list_batches(
    sku: str, uow: unit_of_work.AbstractUnitOfWork
) -> List[Dict[str, object]]:
    with uow:
        product = uow.products.get(sku)
        batches = [
            {"ref": batch.reference, "eta": batch.eta} for batch in product.batches
        ]
        return batches


def add_batch(
    ref: str, sku: str, qty: int, eta: date, uow: unit_of_work.AbstractUnitOfWork
) -> str:
    with uow:
        product = uow.products.get(sku)
        if product:
            batch = model.Batch(ref, sku, qty, eta)
            product.order_batches([batch])
            uow.commit()
            return batch.sku
        raise errors.InvalidSku(f"Invalid sku {sku}")


def edit_batch(
    sku: str, ref: str, eta: date, uow: unit_of_work.AbstractUnitOfWork
) -> str:
    with uow:
        product = uow.products.get(sku)
        if product:
            batch = None
            for b in product.batches:
                if ref == b.reference:
                    batch = b
                    break
            if batch:
                batch.eta = eta
                uow.commit()
                return batch.reference
            raise errors.InvalidBatchRef(f"Invalid batch ref {ref}")
        raise errors.InvalidSku(f"Invalid sku {sku}")
