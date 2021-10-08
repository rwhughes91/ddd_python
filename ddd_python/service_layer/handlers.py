from typing import List, Optional, Union

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


def add_product(
    command: commands.CreateProduct,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = model.Product(command.sku, [])
        uow.products.add(product)
        uow.commit()
        return product.sku


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


def deallocate(command: commands.Deallocate, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        line = model.OrderLine(command.orderid, command.sku, command.qty)
        product = uow.products.get_by_batchref(batchref=command.ref)
        product.deallocate(ref=command.ref, line=line)
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


def publish_product_created_event(
    event: events.ProductCreated,
    uow: unit_of_work.AbstractUnitOfWork,
    queue: Optional[Messages],
):
    uow.event_publisher.publish("product_created", event)


def add_product_to_read_model(
    event: events.ProductCreated,
    uow: unit_of_work.AbstractUnitOfWork,
    queue: Optional[Messages],
):
    with uow:
        uow.execute(
            """
            INSERT INTO products_view (sku)
            VALUES (:sku)
            """,
            {"sku": event.sku},
        )
        uow.commit()


def publish_batch_created_event(
    event: events.BatchCreated,
    uow: unit_of_work.AbstractUnitOfWork,
    queue: Optional[Messages],
):
    uow.event_publisher.publish("batch_created", event)


def add_batch_to_read_model(
    event: events.BatchCreated,
    uow: unit_of_work.AbstractUnitOfWork,
    queue: Optional[Messages],
):
    with uow:
        uow.execute(
            """
            INSERT INTO batches_view (sku, reference, eta)
            VALUES (:sku, :reference, :eta)
            """,
            {"sku": event.sku, "reference": event.reference, "eta": event.eta},
        )
        uow.commit()
