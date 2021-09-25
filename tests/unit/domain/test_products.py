from datetime import date, timedelta

import pytest

from ddd_python.domain import model

# ALLOCATIONS


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


def test_version_number_incremented_when_allocated():
    batch = model.Batch("batch1", "SMALL-FORK", 10, eta=date.today())
    product = model.Product("SMALL-FORK", [batch])
    assert product.version_number == 0

    product.allocate(model.OrderLine("order1", "SMALL-FORK", 10))
    assert product.version_number == 1


# ORDERING


def test_batches_are_added():
    product = model.Product("SMALL-FORK", [])
    batch = model.Batch("batch1", "SMALL-FORK", 10, eta=date.today())

    assert product.batches == []

    product.order_batches([batch])

    assert product.batches == [batch]


def test_raises_invalid_eta_exception_if_batch_eta_in_past():
    product = model.Product("SMALL-FORK", [])
    batch = model.Batch(
        "batch1", "SMALL-FORK", 10, eta=date(year=1970, month=12, day=1)
    )

    with pytest.raises(model.InvalidETA):
        product.order_batches([batch])


def test_duplicate_batches_are_ignored():
    batch = model.Batch("batch1", "SMALL-FORK", 10, eta=date.today())
    product = model.Product("SMALL-FORK", [batch])

    assert product.batches == [batch]

    product.order_batches([batch])

    assert product.batches == [batch]


def test_raises_invalid_sku_exception_if_batch_sku_does_not_match_product_sku():
    product = model.Product("SMALL-FORK", [])
    batch = model.Batch("batch1", "SMALL-FORKY-SILVER", 10, eta=date.today())

    with pytest.raises(model.InvalidSku, match="SMALL-FORK"):
        product.order_batches([batch])


def test_version_number_incremented_when_bathes_ordered():
    product = model.Product("SMALL-FORK", [])
    assert product.version_number == 0

    batch = model.Batch("batch1", "SMALL-FORK", 10, eta=date.today())
    product.order_batches([batch])
    assert product.version_number == 1
