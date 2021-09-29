from datetime import datetime

from flask import Flask, request

from ddd_python.adapters import email, orm
from ddd_python.domain import events
from ddd_python.service_layer import unit_of_work
from ddd_python.service_layer.messagebus import MessageBus

orm.start_mappers()
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    uow = unit_of_work.SqlAlchemyUnitOfWork(email.FakeEmailAdapter())
    messagebus = MessageBus(uow)
    results = messagebus.handle(
        events.AllocationRequired(
            request.json.get("orderid"),
            request.json.get("sku"),
            request.json.get("qty"),
        )
    )
    batchref = results.pop(0)
    return {"batchref": batchref}, 201


@app.route("/products", methods=["GET"])
def list_products():
    uow = unit_of_work.SqlAlchemyUnitOfWork(email.FakeEmailAdapter())
    messagebus = MessageBus(uow)
    results = messagebus.handle(events.ProductsRequired())
    products = results.pop(0)
    return {"products": products}, 200


@app.route("/products", methods=["POST"])
def add_products():
    uow = unit_of_work.SqlAlchemyUnitOfWork(email.FakeEmailAdapter())
    messagebus = MessageBus(uow)
    results = messagebus.handle(events.ProductCreated(request.json.get("sku")))
    productref = results.pop(0)
    return {"productref": productref}, 201


@app.route("/batches/<sku>", methods=["GET"])
def list_batches(sku):
    uow = unit_of_work.SqlAlchemyUnitOfWork(email.FakeEmailAdapter())
    messagebus = MessageBus(uow)
    results = messagebus.handle(events.BatchesRequired(sku))
    batches = results.pop(0)
    return {"batches": batches}, 200


@app.route("/batches", methods=["POST"])
def add_batch():
    uow = unit_of_work.SqlAlchemyUnitOfWork(email.FakeEmailAdapter())
    messagebus = MessageBus(uow)
    date = datetime.strptime(request.json.get("eta"), "%m/%d/%Y").date()
    results = messagebus.handle(
        events.BatchCreated(
            request.json.get("ref"),
            request.json.get("sku"),
            request.json.get("qty"),
            date,
        )
    )
    batchref = results.pop(0)

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["PUT"])
def edit_batch():
    uow = unit_of_work.SqlAlchemyUnitOfWork(email.FakeEmailAdapter())
    messagebus = MessageBus(uow)
    results = messagebus.handle(
        events.BatchQuantityChanged(request.json.get("ref"), request.json.get("qty"))
    )
    batchref = results.pop(0)
    return {"batchref": batchref}, 200


if __name__ == "__main__":
    app.run(port=5000)
