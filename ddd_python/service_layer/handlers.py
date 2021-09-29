from typing import Dict, List

from ddd_python.domain import events, model

from . import errors, unit_of_work


def allocate(
    event: events.AllocationRequired,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = model.OrderLine(event.orderid, event.sku, event.qty)
    with uow:
        product = uow.products.get(event.sku)
        if product:
            batch_ref = product.allocate(line)
            uow.commit()
            return batch_ref
        raise errors.InvalidSku(f"Invalid sku {event.sku}")


def list_products(event: events.ProductsRequired, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        products = uow.products.list()
        return [{"sku": product.sku} for product in products]


def add_product(event: events.ProductCreated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = model.Product(event.sku, [])
        uow.products.add(product)
        uow.commit()
        return product.sku


def list_batches(
    event: events.BatchesRequired, uow: unit_of_work.AbstractUnitOfWork
) -> List[Dict[str, object]]:
    with uow:
        product = uow.products.get(event.sku)
        batches = [
            {"ref": batch.reference, "eta": batch.eta} for batch in product.batches
        ]
        return batches


def add_batch(event: events.BatchCreated, uow: unit_of_work.AbstractUnitOfWork) -> str:
    with uow:
        product = uow.products.get(event.sku)
        if product:
            batch = model.Batch(event.ref, event.sku, event.qty, event.eta)
            product.add_batches([batch])
            uow.commit()
            return batch.sku
        raise errors.InvalidSku(f"Invalid sku {event.sku}")


def change_batch_quantity(
    event: events.BatchQuantityChanged,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get_by_batchref(batchref=event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()


def send_out_of_stock_notification(
    event: events.OutOfStock, uow: unit_of_work.AbstractUnitOfWork
):
    uow.email.send_mail(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )
