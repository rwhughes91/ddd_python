from . import unit_of_work


def allocations(orderid: str, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        results = uow.execute(
            """
            SELECT sku, batchref FROM allocations_view WHERE orderid = :orderid
            """,
            {"orderid": orderid},
        )
        return [{"sku": result.sku, "batchref": result.batchref} for result in results]
