#!/usr/bin/env python3
from confluent_kafka.admin import AdminClient
from confluent_kafka import Consumer
import json


def print_topic_details(bootstrap_servers: str = "localhost:29092"):
    """Print detailed information about all Kafka topics"""

    admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})

    topics = admin_client.list_topics(timeout=10)
    print("\n=== Kafka Topics ===")

    for topic_name in topics.topics.keys():
        print(f"\nTopic: {topic_name}")

        consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": f"topic_checker_{topic_name}",
                "auto.offset.reset": "earliest",
            }
        )

        consumer.subscribe([topic_name])

        message_count = 0
        messages = []
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                break
            if msg.error():
                print(f"Error: {msg.error()}")
                break
            message_count += 1
            if message_count <= 3:
                try:
                    value = msg.value()
                    if isinstance(value, bytes):
                        value = value.decode("utf-8")
                    messages.append(value)
                except Exception as e:
                    messages.append(f"[Could not decode: {str(e)}]")

        print(f"Messages found: {message_count}")
        if message_count > 0:
            print("Sample messages (up to 3):")
            for idx, msg in enumerate(messages, 1):
                print(f"  Message {idx}: {msg[:200]}...")

        consumer.close()


if __name__ == "__main__":
    print_topic_details()
