#!/bin/bash

# Set variables
MINIO_ALIAS="retail-minio"
BUCKET_NAME="retail-data"

# Reset any existing webhook configurations
mc admin config reset $MINIO_ALIAS notify_webhook

# Configure webhook
mc admin config set $MINIO_ALIAS notify_webhook:customer \
    endpoint="http://host.docker.internal:7203/minio/events" \
    enable="on" \
    queue_limit="10000"

# Restart MinIO to apply changes
mc admin service restart $MINIO_ALIAS

# Wait for MinIO to restart
echo "Waiting for MinIO to restart..."
sleep 5

# Add event notification for the bucket
mc event add $MINIO_ALIAS/$BUCKET_NAME arn:minio:sqs:::customer \
    --event put,delete \
    --prefix "customers/"

# Verify configuration
echo -e "\nWebhook Configuration:"
mc admin config get $MINIO_ALIAS notify_webhook

echo -e "\nEvent Configuration:"
mc event list $MINIO_ALIAS/$BUCKET_NAME#!/bin/bash

# Set variables
MINIO_ALIAS="retail-minio"
BUCKET_NAME="retail-data"

# Reset any existing webhook configurations
mc admin config reset $MINIO_ALIAS notify_webhook

# Configure webhook
mc admin config set $MINIO_ALIAS notify_webhook:customer \
    endpoint="http://host.docker.internal:7203/minio/events" \
    enable="on" \
    queue_limit="10000"

# Restart MinIO to apply changes
mc admin service restart $MINIO_ALIAS

# Wait for MinIO to restart
echo "Waiting for MinIO to restart..."
sleep 5

# Add event notification for the bucket
mc event add $MINIO_ALIAS/$BUCKET_NAME arn:minio:sqs:::customer \
    --event put,delete \
    --prefix "customers/"

# Verify configuration
echo -e "\nWebhook Configuration:"
mc admin config get $MINIO_ALIAS notify_webhook

echo -e "\nEvent Configuration:"
mc event list $MINIO_ALIAS/$BUCKET_NAME
