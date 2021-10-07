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


def products(uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        products = uow.execute(
            """
            SELECT sku FROM products_view
            """
        )
        return [{"sku": product.sku} for product in products]


def batches(sku: str, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        batches = uow.execute(
            """
            SELECT reference, eta FROM batches_view WHERE sku = :sku
            """,
            {"sku": sku},
        )
        return [{"ref": batch.reference, "eta": batch.eta} for batch in batches]
