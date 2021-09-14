from datetime import date

from ddd_python.models import Batch, OrderLine
from ddd_python.repository import SqlAlchemyRepository


def insert_orderline(session):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty)"
        ' VALUES ("order1", "GENERIC-SOFA", 12)'
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        {"orderid": "order1", "sku": "GENERIC-SOFA"},
    )
    return orderline_id


def insert_batch(session):
    session.execute(
        "INSERT INTO batches (reference, sku, qty, eta)"
        ' VALUES ("batches1", "GENERIC-SOFA", 12, :today)',
        {"today": date.today()},
    )
    [[batch_id]] = session.execute(
        "SELECT id FROM batches WHERE reference=:reference AND sku=:sku",
        {"reference": "batches1", "sku": "GENERIC-SOFA"},
    )
    return batch_id


def test_repository_can_save_a_batch(session):
    batch = Batch("batch1", "RUSTY-SOAPDISH", 100, eta=date.today())

    repo = SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute('SELECT reference, sku, qty, eta FROM "batches"')
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, str(date.today()))]


def test_repository_can_get_a_batch(session):
    reference = "batches1"
    insert_batch(session)
    repo = SqlAlchemyRepository(session)
    batch = repo.get(reference)

    assert batch.reference == reference


def test_repository_can_get_batches(session):
    session.execute(
        "INSERT INTO batches (reference, sku, qty, eta)"
        """VALUES
        ("batches1", "GENERIC-SOFA", 12, :today),
        ("batches2", "GENERIC-SOFA-2", 4, :today)""",
        {"today": date.today()},
    )
    repo = SqlAlchemyRepository(session)
    batches = repo.list()

    assert len(batches) == 2


def test_repository_can_retrieve_a_batch_with_allocations(session):
    orderline_id = insert_orderline(session)
    repo = SqlAlchemyRepository(session)

    batch = Batch("batch1", "RUSTY-SOAPDISH", 100, eta=date.today())
    repo.add(batch)

    orderline = session.query(OrderLine).filter_by(id=orderline_id).first()
    orderline.batch = batch

    session.commit()

    retrieved_batch = repo.get("batch1")

    assert len(retrieved_batch.allocations) == 1
    assert retrieved_batch.allocations[0] == orderline
