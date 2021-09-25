from sqlalchemy import Column, Date, ForeignKey, Integer, MetaData, String, Table
from sqlalchemy.orm import registry, relationship

from ddd_python.domain import model

metadata = MetaData()

mapper_registry = registry()

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("batch_id", Integer, ForeignKey("batches.id")),
    Column("sku", String(255), nullable=False),
    Column("qty", Integer, nullable=False),
    Column("orderid", String(255)),
)

batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("product_id", Integer, ForeignKey("products.id")),
    Column("reference", String(255), nullable=False, unique=True),
    Column("qty", Integer, nullable=False),
    Column("eta", Date, nullable=False),
    Column("sku", String(255), nullable=False),
)

products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255), nullable=False, unique=True),
    Column("version_number", Integer, nullable=False, default=0),
)


def start_mappers():
    mapper_registry.map_imperatively(model.OrderLine, order_lines)
    mapper_registry.map_imperatively(
        model.Batch,
        batches,
        properties={
            "_purchased_quantity": batches.c.qty,
            "allocations": relationship(model.OrderLine, backref="batch"),
        },
    ),
    mapper_registry.map_imperatively(
        model.Product,
        products,
        properties={"batches": relationship(model.Batch, backref="product")},
    )


def clear_mappers():
    mapper_registry.dispose()
