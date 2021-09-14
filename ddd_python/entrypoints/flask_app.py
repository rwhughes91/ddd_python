from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ddd_python import config
from ddd_python.adapters import orm, repository
from ddd_python.domain import model
from ddd_python.service_layer import services

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.postgres_uri))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    line = model.OrderLine(
        request.json.get("orderid"), request.json.get("sku"), request.json.get("qty")
    )
    batchref = services.allocate_order(line, repo, session)

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["GET"])
def list_batches():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    batches = services.list_batches(repo)

    return {"batches": [batch.reference for batch in batches]}, 200


@app.route("/batches", methods=["POST"])
def add_batch():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    batch = model.Batch(
        request.json.get("ref"),
        request.json.get("sku"),
        request.json.get("qty"),
        request.json.get("eta"),
    )
    batchref = services.add_batch(batch, repo, session)

    return {"batchref": batchref}, 201


if __name__ == "__main__":
    app.run(port=5000)
