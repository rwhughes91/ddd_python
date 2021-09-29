from datetime import datetime

from flask import Flask, request

from ddd_python.adapters import email, orm
from ddd_python.domain import events
from ddd_python.service_layer import messagebus, unit_of_work

orm.start_mappers()
app = Flask(__name__)

uow = unit_of_work.SqlAlchemyUnitOfWork(email.FakeEmailAdapter())


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    results = messagebus.handle(
        events.AllocationRequired(
            request.json.get("orderid"),
            request.json.get("sku"),
            request.json.get("qty"),
        ),
        uow,
    )
    batchref = results.pop(0)
    return {"batchref": batchref}, 201


@app.route("/products", methods=["GET"])
def list_products():
    results = messagebus.handle(events.ProductsRequired(), uow)
    products = results.pop(0)
    return {"products": products}, 200


@app.route("/products", methods=["POST"])
def add_products():
    results = messagebus.handle(events.ProductCreated(request.json.get("sku")), uow)
    productref = results.pop(0)
    return {"productref": productref}, 201


@app.route("/batches/<sku>", methods=["GET"])
def list_batches(sku):
    results = messagebus.handle(events.BatchesRequired(sku), uow)
    batches = results.pop(0)
    return {"batches": batches}, 200


@app.route("/batches", methods=["POST"])
def add_batch():
    date = datetime.strptime(request.json.get("eta"), "%m/%d/%Y").date()
    results = messagebus.handle(
        events.BatchCreated(
            request.json.get("ref"),
            request.json.get("sku"),
            request.json.get("qty"),
            date,
        ),
        uow,
    )
    batchref = results.pop(0)

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["PUT"])
def edit_batch():
    results = messagebus.handle(
        events.BatchEdited(
            request.json.get("sku"), request.json.get("ref"), request.json.get("eta")
        ),
        uow,
    )
    batchref = results.pop(0)
    return {"batchref": batchref}, 200


if __name__ == "__main__":
    app.run(port=5000)
