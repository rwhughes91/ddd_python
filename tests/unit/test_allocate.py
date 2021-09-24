from datetime import date, timedelta

import pytest

from ddd_python.domain import model


def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = model.Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = model.Batch(
        "shipment-batch", "RETRO-CLOCK", 100, eta=date.today() + timedelta(days=1)
    )
    line = model.OrderLine("oref", "RETRO-CLOCK", 10)

    product = model.Product("RETRO-CLOCK", [in_stock_batch, shipment_batch])
    product.allocate(line)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    earliest = model.Batch("speedy-batch", "MINIMALIST-SPOON", 100, eta=date.today())
    medium = model.Batch(
        "normal-batch", "MINIMALIST-SPOON", 100, eta=date.today() + timedelta(days=1)
    )
    latest = model.Batch(
        "slow-batch", "MINIMALIST-SPOON", 100, eta=date.today() + timedelta(days=2)
    )
    line = model.OrderLine("order1", "MINIMALIST-SPOON", 10)

    product = model.Product("MINIMALIST-SPOON", [medium, earliest, latest])
    product.allocate(line)

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref():
    in_stock_batch = model.Batch("in-stock-batch-ref", "HIGHBROW-POSTER", 100, eta=None)
    shipment_batch = model.Batch(
        "shipment-batch-ref",
        "HIGHBROW-POSTER",
        100,
        eta=date.today() + timedelta(days=1),
    )
    line = model.OrderLine("oref", "HIGHBROW-POSTER", 10)
    product = model.Product("HIGHBROW-POSTER", [in_stock_batch, shipment_batch])
    allocation = product.allocate(line)

    assert allocation == in_stock_batch.reference


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = model.Batch("batch1", "SMALL-FORK", 10, eta=date.today())
    product = model.Product("SMALL-FORK", [batch])
    product.allocate(model.OrderLine("order1", "SMALL-FORK", 10))

    with pytest.raises(model.OutOfStock, match="SMALL-FORK"):
        product.allocate(model.OrderLine("order2", "SMALL-FORK", 1))
