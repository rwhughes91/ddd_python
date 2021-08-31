from sqlalchemy import Column, Date, ForeignKey, Integer, MetaData, String, Table
from sqlalchemy.orm import registry, relationship

from .models import Batch, OrderLine

metadata = MetaData()

mapper_registry = registry()

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255), nullable=False),
    Column("qty", Integer, nullable=False),
    Column("orderid", String(255)),
    Column("batch_id", Integer, ForeignKey("batches.id")),
)

batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255), nullable=False, unique=True),
    Column("qty", Integer, nullable=False),
    Column("eta", Date, nullable=False),
    Column("sku", String(255), nullable=False),
)


def start_mappers():
    mapper_registry.map_imperatively(OrderLine, order_lines)
    mapper_registry.map_imperatively(
        Batch,
        batches,
        properties={
            "_purchased_quantity": batches.c.qty,
            "_allocations": relationship(OrderLine, backref="batch"),
        },
    ),


def clear_mappers():
    mapper_registry.dispose()
