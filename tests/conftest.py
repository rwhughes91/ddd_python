import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ddd_python.orm import clear_mappers, metadata, start_mappers


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    start_mappers()
    with Session(engine) as session:
        yield session
    clear_mappers()
    metadata.drop_all(engine)
