#!/bin/bash

MINIO_ALIAS="retail-minio"
BUCKET_NAME="retail-data"
WEBHOOK_URL="http://localhost:7203"
NOTIFICATION_NAME="customers-webhook"  

if ! command -v mc &> /dev/null
then
    echo "MinIO Client (mc) could not be found. Please install it first."
    exit 1
fi

# echo "Creating bucket: $BUCKET_NAME"
# mc mb $MINIO_ALIAS/$BUCKET_NAME

echo "Setting public read policy for bucket"
mc policy set download $MINIO_ALIAS/$BUCKET_NAME

echo "Setting up webhook notification for PUT events"
mc admin config set $MINIO_ALIAS notify_webhook:$NOTIFICATION_NAME endpoint=$WEBHOOK_URL
mc admin service restart $MINIO_ALIAS  

echo "Enabling notification on bucket for PUT events"
mc event add $MINIO_ALIAS/$BUCKET_NAME arn:minio:sqs:::$NOTIFICATION_NAME --event put --prefix 'customers/'

# Verify notification setup
echo "Verifying notification configuration"
mc event list $MINIO_ALIAS/$BUCKET_NAME

echo "Setup complete!"
