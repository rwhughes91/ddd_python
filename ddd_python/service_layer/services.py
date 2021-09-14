from typing import List

from sqlalchemy.orm import Session

from ddd_python.adapters import repository
from ddd_python.domain import model

from .errors import InvalidSku


def allocate_order(
    line: model.OrderLine, repo: repository.AbstractRepository, session: Session
) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batch_ref = model.allocate(line, batches)
    session.commit()
    return batch_ref


def list_batches(repo: repository.AbstractRepository) -> List[model.Batch]:
    return repo.list()


def add_batch(
    batch: model.Batch, repo: repository.AbstractRepository, session: Session
) -> str:
    repo.add(batch)
    session.commit()
    return batch.reference


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}
