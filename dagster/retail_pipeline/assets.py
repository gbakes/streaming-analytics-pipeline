import json
import os
from datetime import datetime

from minio import Minio

import dagster as dg


def get_minio_client():
    return Minio(
        os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
        secure=False,
    )


@dg.asset
def customers_raw(context: dg.AssetExecutionContext):
    try:
        if not context.op_config:
            context.log.info("No configuration provided")
            return

        context.log.info("Debug - Full context config:")
        context.log.info(json.dumps(context.op_config, indent=2))
        context.log.info(
            f"Processing customer data from {context.op_config.get('object_path')}"
        )
    except Exception as e:
        context.log.error(f"Error processing customer data: {str(e)}")
        raise


@dg.asset
def products_raw(context: dg.AssetExecutionContext):
    try:
        if not context.op_config:
            context.log.info("No configuration provided")
            return

        context.log.info("Debug - Full context config:")
        context.log.info(json.dumps(context.op_config, indent=2))
        context.log.info(
            f"Processing product data from {context.op_config.get('object_path')}"
        )
    except Exception as e:
        context.log.error(f"Error processing product data: {str(e)}")
        raise


customers_job = dg.define_asset_job("customers_job", selection=[customers_raw])
products_job = dg.define_asset_job("products_job", selection=[products_raw])


@dg.sensor(
    job=customers_job,
    minimum_interval_seconds=30,
)
def customer_data_sensor(context: dg.SensorEvaluationContext):
    client = get_minio_client()
    bucket_name = "retail-data"
    prefix = "topics/postgres-server.public.customers/customers/"

    try:
        context.log.info(f"Debug - Current cursor value: {context.cursor}")
        objects = list(client.list_objects(bucket_name, prefix=prefix, recursive=True))
        context.log.info(f"Found {len(objects)} objects in {prefix}")

        if objects:
            last_processed = context.cursor or "0"
            context.log.info(f"Debug - Last processed timestamp: {last_processed}")

            sorted_objects = sorted(
                objects, key=lambda obj: obj.last_modified, reverse=True
            )

            if sorted_objects:
                first_obj = sorted_objects[0]
                clean_path = clean_object_path(first_obj.object_name, "customers")
                context.log.info(f"Debug - Latest object details:")
                context.log.info(f"  Original path: {first_obj.object_name}")
                context.log.info(f"  Clean path: {clean_path}")
                context.log.info(f"  Modified: {first_obj.last_modified}")

            for obj in sorted_objects:
                file_timestamp = obj.last_modified.timestamp()
                if str(file_timestamp) <= last_processed:
                    context.log.info(
                        f"Skipping already processed file: {obj.object_name}"
                    )
                    continue

                clean_path = clean_object_path(obj.object_name, "customers")
                file_key = clean_path.split("/")[-1].split(".")[0]
                context.log.info(f"Processing new file: {clean_path}")

                yield dg.RunRequest(
                    run_key=file_key,
                    run_config={
                        "ops": {
                            "customers_raw": {
                                "config": {
                                    "object_path": obj.object_name,
                                    "clean_path": clean_path,
                                    "last_modified": obj.last_modified.isoformat(),
                                }
                            }
                        }
                    },
                    tags={"minio_path": clean_path},
                )

            if sorted_objects:
                new_cursor = str(sorted_objects[0].last_modified.timestamp())
                context.log.info(f"Debug - Updating cursor to: {new_cursor}")
                context.update_cursor(new_cursor)

        else:
            context.log.info("No new files found in customers prefix")
            yield dg.SkipReason("No customer data files found")

    except Exception as e:
        context.log.error(f"Error checking MinIO: {str(e)}")
        yield dg.SkipReason(f"Error: {str(e)}")


def clean_object_path(obj_name: str, data_type: str) -> str:
    """Convert full path to clean path format"""
    parts = obj_name.split("/")
    try:
        year_idx = next(
            i for i, part in enumerate(parts) if len(part) == 4 and part.isdigit()
        )
        date_parts = parts[year_idx : year_idx + 4]  # year, month, day, hour
        filename = parts[-1]
        return f"{data_type}/{'/'.join(date_parts)}/{filename}"
    except (StopIteration, IndexError):
        return obj_name


@dg.sensor(
    job=products_job,
    minimum_interval_seconds=30,
)
def product_data_sensor(context: dg.SensorEvaluationContext):
    client = get_minio_client()
    bucket_name = "retail-data"
    prefix = "topics/postgres-server.public.products/products/"

    try:
        context.log.info(f"Debug - Current cursor value: {context.cursor}")
        objects = list(client.list_objects(bucket_name, prefix=prefix, recursive=True))
        context.log.info(f"Found {len(objects)} objects in {prefix}")

        if objects:
            last_processed = context.cursor or "0"
            context.log.info(f"Debug - Last processed timestamp: {last_processed}")

            sorted_objects = sorted(
                objects, key=lambda obj: obj.last_modified, reverse=True
            )

            if sorted_objects:
                first_obj = sorted_objects[0]
                clean_path = clean_object_path(first_obj.object_name, "products")
                context.log.info(f"Debug - Latest object details:")
                context.log.info(f"  Original path: {first_obj.object_name}")
                context.log.info(f"  Clean path: {clean_path}")
                context.log.info(f"  Modified: {first_obj.last_modified}")

            for obj in sorted_objects:
                file_timestamp = obj.last_modified.timestamp()
                if str(file_timestamp) <= last_processed:
                    context.log.info(
                        f"Skipping already processed file: {obj.object_name}"
                    )
                    continue

                clean_path = clean_object_path(obj.object_name, "products")
                file_key = clean_path.split("/")[-1].split(".")[0]
                context.log.info(f"Processing new file: {clean_path}")

                yield dg.RunRequest(
                    run_key=file_key,
                    run_config={
                        "ops": {
                            "products_raw": {
                                "config": {
                                    "object_path": obj.object_name,
                                    "clean_path": clean_path,
                                    "last_modified": obj.last_modified.isoformat(),
                                }
                            }
                        }
                    },
                    tags={"minio_path": clean_path},
                )

            if sorted_objects:
                new_cursor = str(sorted_objects[0].last_modified.timestamp())
                context.log.info(f"Debug - Updating cursor to: {new_cursor}")
                context.update_cursor(new_cursor)

        else:
            context.log.info("No new files found in products prefix")
            yield dg.SkipReason("No product data files found")

    except Exception as e:
        context.log.error(f"Error checking MinIO: {str(e)}")
        yield dg.SkipReason(f"Error: {str(e)}")


defs = dg.Definitions(
    assets=[customers_raw, products_raw],
    jobs=[customers_job, products_job],
    sensors=[customer_data_sensor, product_data_sensor],
)
