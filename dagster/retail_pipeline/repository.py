from dagster import repository
from retail_pipeline.assets import (
    customer_data_sensor,
    customers_job,
    customers_raw,
    product_data_sensor,
    products_job,
    products_raw,
)


@repository
def retail_data_repo():
    """Data pipeline repository for retail data"""
    return [
        # Assets
        customers_raw,
        products_raw,
        # Jobs
        customers_job,
        products_job,
        # Sensors
        customer_data_sensor,
        product_data_sensor,
    ]
