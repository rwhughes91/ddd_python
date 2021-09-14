import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ddd_python.adapters import orm


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    orm.metadata.create_all(engine)
    orm.start_mappers()
    with Session(engine) as session:
        yield session
    orm.clear_mappers()
    orm.metadata.drop_all(engine)
