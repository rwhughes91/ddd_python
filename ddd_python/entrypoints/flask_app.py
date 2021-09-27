from datetime import datetime

from flask import Flask, request

from ddd_python.adapters import email, orm
from ddd_python.service_layer import messagebus, services, unit_of_work

orm.start_mappers()
app = Flask(__name__)


bus = messagebus.MessageBus(email.FakeEmailAdapter())


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    uow = unit_of_work.SqlAlchemyUnitOfWork(bus)
    batchref = services.allocate(
        request.json.get("orderid"),
        request.json.get("sku"),
        request.json.get("qty"),
        uow,
    )

    return {"batchref": batchref}, 201


@app.route("/products", methods=["GET"])
def list_products():
    uow = unit_of_work.SqlAlchemyUnitOfWork(bus)
    products = services.list_products(uow)
    return {"products": products}, 200


@app.route("/products", methods=["POST"])
def add_products():
    uow = unit_of_work.SqlAlchemyUnitOfWork(bus)
    productref = services.add_product(request.json.get("sku"), uow)
    return {"productref": productref}, 201


@app.route("/batches/<sku>", methods=["GET"])
def list_batches(sku):
    uow = unit_of_work.SqlAlchemyUnitOfWork(bus)
    batches = services.list_batches(sku, uow)

    return {"batches": batches}, 200


@app.route("/batches", methods=["POST"])
def add_batch():
    date = datetime.strptime(request.json.get("eta"), "%m/%d/%Y").date()
    uow = unit_of_work.SqlAlchemyUnitOfWork(bus)
    batchref = services.add_batch(
        request.json.get("ref"),
        request.json.get("sku"),
        request.json.get("qty"),
        date,
        uow,
    )

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["PUT"])
def edit_batch():
    uow = unit_of_work.SqlAlchemyUnitOfWork(bus)
    batchref = services.edit_batch(
        request.json.get("sku"),
        request.json.get("ref"),
        request.json.get("eta"),
        uow,
    )

    return {"batchref": batchref}, 200


if __name__ == "__main__":
    app.run(port=5000)
