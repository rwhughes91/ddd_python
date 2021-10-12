import json

from redis import Redis

if __name__ == "__main__":
    r = Redis(
        host="localhost",
        port=6380,
    )

    r.publish("add_products", json.dumps({"sku": "GENERIC-SOFA-01"}))
    r.publish(
        "add_batch",
        json.dumps({"ref": "batch-001", "sku": "GENERIC-SOFA-01", "qty": 10}),
    )
    r.publish(
        "allocate",
        json.dumps({"orderid": "orderline-001", "sku": "GENERIC-SOFA-01", "qty": 1}),
    )
