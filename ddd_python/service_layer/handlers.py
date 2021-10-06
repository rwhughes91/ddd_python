from typing import Dict, List, Optional, Union

from ddd_python.domain import commands, events, model

from . import errors, unit_of_work

Message = Union[commands.Command, events.Event]
Messages = List[Message]

# COMMANDS


def allocate(
    command: commands.Allocate,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = model.OrderLine(command.orderid, command.sku, command.qty)
    with uow:
        product = uow.products.get(command.sku)
        if product:
            batch_ref = product.allocate(line)
            uow.commit()
            return batch_ref
        raise errors.InvalidSku(f"Invalid sku {command.sku}")


def list_products(
    command: commands.GetProducts,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        products = uow.products.list()
        return [{"sku": product.sku} for product in products]


def add_product(
    command: commands.CreateProduct,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = model.Product(command.sku, [])
        uow.products.add(product)
        uow.commit()
        return product.sku


def list_batches(
    command: commands.GetBatches,
    uow: unit_of_work.AbstractUnitOfWork,
) -> List[Dict[str, object]]:
    with uow:
        product = uow.products.get(command.sku)
        batches = [
            {"ref": batch.reference, "eta": batch.eta} for batch in product.batches
        ]
        return batches


def add_batch(
    command: commands.CreateBatch,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    with uow:
        product = uow.products.get(command.sku)
        if product:
            batch = model.Batch(command.ref, command.sku, command.qty, command.eta)
            product.add_batches([batch])
            uow.commit()
            return batch.sku
        raise errors.InvalidSku(f"Invalid sku {command.sku}")


def change_batch_quantity(
    command: commands.ChangeBatchQuantity,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get_by_batchref(batchref=command.ref)
        product.change_batch_quantity(ref=command.ref, qty=command.qty)
        uow.commit()


# EVENTS


def send_out_of_stock_notification(
    event: events.OutOfStock,
    uow: unit_of_work.AbstractUnitOfWork,
    queue: Optional[Messages],
):
    uow.email.send_mail(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )


def publish_allocated_event(
    event: events.Allocated,
    uow: unit_of_work.AbstractUnitOfWork,
    queue: Optional[Messages],
):
    uow.event_publisher.publish("line_allocated", event)


def publish_deallocated_event(
    event: events.Allocated,
    uow: unit_of_work.AbstractUnitOfWork,
    queue: Optional[Messages],
):
    uow.event_publisher.publish("line_deallocated", event)


def add_allocation_to_read_model(
    event: events.Allocated,
    uow: unit_of_work.AbstractUnitOfWork,
    queue: Optional[Messages],
):
    with uow:
        uow.execute(
            """
            INSERT INTO allocations_view (orderid, sku, batchref)
            VALUES (:orderid, :sku, :batchref)
            """,
            {"orderid": event.orderid, "sku": event.sku, "batchref": event.batchref},
        )
        uow.commit()


def remove_allocation_from_read_model(
    event: events.Deallocated,
    uow: unit_of_work.AbstractUnitOfWork,
    queue: Optional[Messages],
):
    with uow:
        uow.execute(
            """
            DELETE FROM allocations_view
            WHERE orderid = :orderid AND sku = :sku
            """,
            {"orderid": event.orderid, "sku": event.sku},
        )
        uow.commit()
