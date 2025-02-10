#!/usr/bin/env python3
import os
from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv
import time


def check_kafka_topics():
    conf = {
        "bootstrap.servers": "localhost:29092",
        "group.id": "kafka-debugger",
        "auto.offset.reset": "earliest",
    }

    consumer = Consumer(conf)
    topics = [
        "postgres-server.public.customers",
        "postgres-server.public.products",
        "postgres-server.public.orders",
        "postgres-server.public.order_items",
    ]

    try:
        for topic in topics:
            print(f"\nChecking topic: {topic}")

            consumer.subscribe([topic])

            msg_count = 0
            start_time = time.time()

            while True:
                if time.time() - start_time > 5:
                    break

                msg = consumer.poll(1.0)

                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        break
                    else:
                        print(f"Error: {msg.error()}")
                        break

                msg_count += 1
                if msg_count == 1:
                    print(f"Sample message: {msg.value()}")

            print(f"Found {msg_count} messages")

            consumer.unsubscribe()

    finally:
        consumer.close()


if __name__ == "__main__":
    check_kafka_topics()
