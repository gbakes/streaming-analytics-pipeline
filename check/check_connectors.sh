#!/bin/bash

CONNECT_URL="http://localhost:8084"

echo "Testing Kafka Connect access..."
curl -s $CONNECT_URL

echo -e "\n\nListing all connectors..."
curl -s $CONNECT_URL/connectors

echo -e "\n\nChecking status of all connectors..."
curl -s "$CONNECT_URL/connectors?expand=status"

echo -e "\n\nChecking specific connectors..."
CONNECTORS=("postgres-connector" "customers-s3-sink" "products-s3-sink" "orders-s3-sink" "order-items-s3-sink")

for connector in "${CONNECTORS[@]}"; do
    echo -e "\nChecking $connector..."
    echo "Config:"
    curl -s "$CONNECT_URL/connectors/$connector/config"
    echo -e "\nStatus:"
    curl -s "$CONNECT_URL/connectors/$connector/status"
done