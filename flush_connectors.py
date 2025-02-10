#!/usr/bin/env python3
import requests
import time
from typing import List


def flush_connectors(
    connect_url: str = "http://localhost:8084", connectors: List[str] = None
):
    """
    Flush connectors by pausing and resuming them
    """
    if connectors is None:
        response = requests.get(f"{connect_url}/connectors")
        connectors = response.json()

    for connector in connectors:
        print(f"\nFlushing connector: {connector}")
        print(f"Pausing {connector}...")
        response = requests.put(f"{connect_url}/connectors/{connector}/pause")
        if response.status_code == 202:
            print(f"Successfully paused {connector}")
        else:
            print(
                f"Failed to pause {connector}: {response.status_code} - {response.text}"
            )
            continue

        time.sleep(2)

        print(f"Resuming {connector}...")
        response = requests.put(f"{connect_url}/connectors/{connector}/resume")
        if response.status_code == 202:
            print(f"Successfully resumed {connector}")
        else:
            print(
                f"Failed to resume {connector}: {response.status_code} - {response.text}"
            )


if __name__ == "__main__":
    sink_connectors = [
        "customers-s3-sink",
        "products-s3-sink",
        "orders-s3-sink",
        "order-items-s3-sink",
    ]

    flush_connectors(connectors=sink_connectors)
