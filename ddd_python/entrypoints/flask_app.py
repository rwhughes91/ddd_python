from flask import Flask, request

from ddd_python.adapters import orm
from ddd_python.service_layer import services, unit_of_work

orm.start_mappers()
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    batchref = services.allocate(
        request.json.get("orderid"),
        request.json.get("sku"),
        request.json.get("qty"),
        uow,
    )

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["GET"])
def list_batches():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    batches = services.list_batches(request.json.get("sku"), uow)

    return {"batches": batches}, 200


@app.route("/batches", methods=["POST"])
def add_batch():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    batchref = services.add_batch(
        request.json.get("ref"),
        request.json.get("sku"),
        request.json.get("qty"),
        request.json.get("eta"),
        uow,
    )

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["PUT"])
def edit_batch():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    batchref = services.edit_batch(
        request.json.get("sku"),
        request.json.get("ref"),
        request.json.get("eta"),
        uow,
    )

    return {"batchref": batchref}, 200


if __name__ == "__main__":
    app.run(port=5000)
