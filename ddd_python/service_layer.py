from sqlalchemy.orm import Session

from .errors import InvalidSku
from .models import OrderLine, allocate
from .repository import AbstractRepository


def allocate_order(line: OrderLine, repo: AbstractRepository, session: Session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batch_ref = allocate(line, batches)
    session.commit()
    return batch_ref


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}
