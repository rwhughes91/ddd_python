from datetime import date

from ddd_python.adapters import repository
from ddd_python.domain import model


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


def insert_product(session):
    session.execute(
        'INSERT INTO products (sku, version_number) VALUES ("GENERIC-SOFA", 0)'
    )
    [[product_id]] = session.execute(
        "SELECT id FROM products WHERE sku=:sku", {"sku": "GENERIC-SOFA"}
    )
    return product_id


def test_repository_can_save_a_product(session):
    batch = model.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=date.today())
    product = model.Product("RUSTY-SOAPDISH", [batch])

    repo = repository.SqlAlchemyProductRepository(session)
    repo.add(product)
    session.commit()

    products = session.execute('SELECT sku FROM "products"')
    batches = session.execute('SELECT reference, sku, qty, eta FROM "batches"')
    assert list(products) == [("RUSTY-SOAPDISH",)]
    assert list(batches) == [("batch1", "RUSTY-SOAPDISH", 100, str(date.today()))]


def test_repository_can_get_a_product(session):
    sku = "GENERIC-SOFA"
    insert_product(session)
    repo = repository.SqlAlchemyProductRepository(session)
    product = repo.get(sku)

    assert product.sku == sku


def test_repository_can_get_products(session):
    session.execute(
        "INSERT INTO products (sku, version_number)"
        """VALUES
        ("GENERIC-SOFA", 0),
        ("GENERIC-SOFA-2", 0)""",
    )
    repo = repository.SqlAlchemyProductRepository(session)
    products = repo.list()

    assert len(products) == 2


def test_repository_can_retrieve_a_batch_with_allocations(session):
    orderline_id = insert_orderline(session)
    batch_id = insert_batch(session)
    product_id = insert_product(session)

    product = session.query(model.Product).filter_by(id=product_id).first()
    batch = session.query(model.Batch).filter_by(id=batch_id).first()
    batch.product = product
    orderline = session.query(model.OrderLine).filter_by(id=orderline_id).first()
    orderline.batch = batch

    session.commit()

    repo = repository.SqlAlchemyProductRepository(session)

    retrieved_product = repo.get("GENERIC-SOFA")

    assert len(retrieved_product.batches) == 1
    assert len(retrieved_product.batches[0].allocations) == 1
    assert retrieved_product.batches[0].allocations[0] == orderline
