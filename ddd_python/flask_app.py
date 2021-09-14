from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import config
from .models import OrderLine
from .orm import start_mappers
from .repository import SqlAlchemyRepository
from .service_layer import allocate_order

start_mappers()
get_session = sessionmaker(bind=create_engine(config.postgres_uri))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    line = OrderLine(
        request.json.get("orderid"), request.json.get("sku"), request.json.get("qty")
    )
    repo = SqlAlchemyRepository(session)
    batchref = allocate_order(line, repo, session)

    return {"batchref": batchref}, 201


if __name__ == "__main__":
    app.run(port=5000)
