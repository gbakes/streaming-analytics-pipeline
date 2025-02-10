#!/usr/bin/env python3
import requests
import json
from confluent_kafka.admin import AdminClient
from confluent_kafka import Consumer
import time
from typing import Dict, List
import sys
from minio import Minio
from dotenv import load_dotenv
import os


def check_minio_health(endpoint: str, access_key: str, secret_key: str) -> bool:
    """Check if MinIO is healthy by trying to list buckets"""
    try:
        minio_client = Minio(
            endpoint, access_key=access_key, secret_key=secret_key, secure=False
        )

        minio_client.list_buckets()
        print("MinIO Health Check: OK")
        return True
    except Exception as e:
        print(f"MinIO Health Check Failed: {str(e)}")
        return False


def check_service_health(url: str, service_name: str) -> bool:
    """Check if a service is healthy via HTTP"""
    try:
        response = requests.get(url)
        print(f"{service_name} Health Check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"{service_name} Health Check Failed: {str(e)}")
        return False


def check_kafka_topics(bootstrap_servers: str) -> Dict[str, bool]:
    """Check Kafka topics and their status"""
    admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})

    expected_topics = [
        "postgres-server.public.customers",
        "postgres-server.public.products",
        "postgres-server.public.orders",
        "postgres-server.public.order_items",
        "connect-configs",
        "connect-offsets",
        "connect-status",
    ]

    topic_metadata = admin_client.list_topics(timeout=10)
    existing_topics = topic_metadata.topics.keys()

    results = {}
    for topic in expected_topics:
        exists = topic in existing_topics
        results[topic] = exists
        print(f"Topic {topic}: {'EXISTS' if exists else 'MISSING'}")

        if exists:
            consumer = Consumer(
                {
                    "bootstrap.servers": bootstrap_servers,
                    "group.id": "pipeline-checker",
                    "auto.offset.reset": "earliest",
                }
            )
            consumer.subscribe([topic])
            msg = consumer.poll(1.0)
            has_messages = msg is not None
            print(f"  Has Messages: {has_messages}")
            consumer.close()

    return results


def check_connect_status(connect_url: str) -> Dict[str, str]:
    """Check status of all connectors"""
    try:
        response = requests.get(f"{connect_url}/connectors")
        if response.status_code != 200:
            print(f"Failed to get connectors: {response.status_code}")
            return {}

        connectors = response.json()
        results = {}

        for connector in connectors:
            status_response = requests.get(
                f"{connect_url}/connectors/{connector}/status"
            )
            if status_response.status_code == 200:
                status = status_response.json()
                connector_state = status["connector"]["state"]
                results[connector] = connector_state

                print(f"\nConnector: {connector}")
                print(f"State: {connector_state}")

                if "tasks" in status:
                    for task in status["tasks"]:
                        print(f"Task {task['id']} - State: {task['state']}")
                        if task["state"] == "FAILED":
                            print(f"Error: {task.get('trace', 'No error trace')}")

                config_response = requests.get(
                    f"{connect_url}/connectors/{connector}/config"
                )
                if config_response.status_code == 200:
                    config = config_response.json()
                    print("\nConfiguration:")
                    print(json.dumps(config, indent=2))

        return results
    except Exception as e:
        print(f"Error checking connect status: {str(e)}")
        return {}


def main():
    load_dotenv()

    KAFKA_URL = "localhost:29092"
    CONNECT_URL = "http://localhost:8084"
    MINIO_ENDPOINT = "localhost:9000"
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

    print("\n=== Checking Service Health ===")
    minio_healthy = check_minio_health(
        MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY
    )
    connect_healthy = check_service_health(CONNECT_URL, "Kafka Connect")

    services_healthy = minio_healthy and connect_healthy

    if not services_healthy:
        print("\nOne or more services are unhealthy!")
        sys.exit(1)

    print("\n=== Checking Kafka Topics ===")
    kafka_status = check_kafka_topics(KAFKA_URL)

    print("\n=== Checking Connectors ===")
    connector_status = check_connect_status(CONNECT_URL)

    print("\n=== Pipeline Health Summary ===")
    print("Services:")
    print(f"- Kafka Connect: {'HEALTHY' if connect_healthy else 'UNHEALTHY'}")
    print(f"- MinIO: {'HEALTHY' if minio_healthy else 'UNHEALTHY'}")
    print("\nTopics:")
    for topic, exists in kafka_status.items():
        print(f"- {topic}: {'EXISTS' if exists else 'MISSING'}")
    print("\nConnectors:")
    for connector, state in connector_status.items():
        print(f"- {connector}: {state}")

    if minio_healthy:
        print("\nMinIO Buckets:")
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )
        buckets = minio_client.list_buckets()
        for bucket in buckets:
            print(f"- {bucket.name}")


if __name__ == "__main__":
    main()
