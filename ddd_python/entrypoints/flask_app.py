from datetime import datetime

from flask import Flask, request

from ddd_python.adapters import email, event_publisher, orm
from ddd_python.config import redis_host, redis_port
from ddd_python.domain import commands
from ddd_python.service_layer import unit_of_work, views
from ddd_python.service_layer.messagebus import MessageBus

app = Flask(__name__)

orm.start_mappers()

# Products


@app.route("/products", methods=["POST"])
def add_products():
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    messagebus = MessageBus(uow)
    results = messagebus.handle(commands.CreateProduct(request.json.get("sku")))
    productref = results.pop(0)
    return {"productref": productref}, 201


# Batches


@app.route("/batches", methods=["POST"])
def add_batch():
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    messagebus = MessageBus(uow)
    date = datetime.strptime(request.json.get("eta"), "%m/%d/%Y").date()
    results = messagebus.handle(
        commands.CreateBatch(
            request.json.get("ref"),
            request.json.get("sku"),
            request.json.get("qty"),
            date,
        )
    )
    batchref = results.pop(0)

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["PUT"])
def change_batch_quantity():
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    messagebus = MessageBus(uow)
    results = messagebus.handle(
        commands.ChangeBatchQuantity(request.json.get("ref"), request.json.get("qty"))
    )
    batchref = results.pop(0)
    return {"batchref": batchref}, 200


# Allocations


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    messagebus = MessageBus(uow)
    results = messagebus.handle(
        commands.Allocate(
            request.json.get("orderid"),
            request.json.get("sku"),
            request.json.get("qty"),
        )
    )
    batchref = results.pop(0)
    return {"batchref": batchref}, 201


@app.route("/deallocate", methods=["POST"])
def deallocate():
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    messagebus = MessageBus(uow)
    messagebus.handle(
        commands.Deallocate(
            request.json.get("ref"),
            request.json.get("orderid"),
            request.json.get("sku"),
            request.json.get("qty"),
        )
    )
    return 200


# Views


@app.route("/products", methods=["GET"])
def products_view():
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    return {"products": views.products(uow)}


@app.route("/batches/<sku>", methods=["GET"])
def batches_view(sku):
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    return {"batches": views.batches(sku, uow)}


@app.route("/allocations/<orderid>", methods=["GET"])
def allocations_view(orderid):
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    return {"allocations": views.allocations(orderid, uow)}


if __name__ == "__main__":
    app.run(port=5000)
