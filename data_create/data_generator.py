import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List

import faker
import psycopg2
from psycopg2.extras import execute_values


class DataGenerator:
    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize the data generator with database configuration.
        """
        self.db_config = db_config
        self.fake = faker.Faker()
        self.used_emails = set()
        self.used_skus = set()

    def connect(self) -> psycopg2.extensions.connection:
        """Create and return a database connection."""
        return psycopg2.connect(**self.db_config)

    def generate_unique_email(self) -> str:
        """Generate a unique email address."""
        while True:
            email = f"{self.fake.user_name()}{len(self.used_emails)}@{self.fake.domain_name()}"
            if email not in self.used_emails:
                self.used_emails.add(email)
                return email

    def generate_unique_sku(self) -> str:
        """Generate a unique SKU."""
        while True:
            sku = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if sku not in self.used_skus:
                self.used_skus.add(sku)
                return sku

    def generate_products(self, count: int) -> List[Dict[str, Any]]:
        """Generate product data."""
        products = []
        categories = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports"]
        adjectives = [
            "Premium",
            "Deluxe",
            "Essential",
            "Classic",
            "Professional",
            "Modern",
        ]
        product_types = [
            "Laptop",
            "Smartphone",
            "Headphones",
            "Camera",
            "Watch",
            "Tablet",
            "Shirt",
            "Pants",
            "Jacket",
            "Shoes",
            "Book",
            "Tool Set",
            "Backpack",
        ]

        for _ in range(count):
            name = f"{random.choice(adjectives)} {random.choice(product_types)}"
            product = {
                "name": name,
                "description": self.fake.text(max_nb_chars=200),
                "category": random.choice(categories),
                "price": round(random.uniform(10, 1000), 2),
                "sku": self.generate_unique_sku(),
                "created_at": self.fake.date_time_between(start_date="-1y"),
                "stock_quantity": random.randint(0, 1000),
            }
            products.append(product)

        return products

    def generate_customers(self, count: int) -> List[Dict[str, Any]]:
        """Generate customer data."""
        customers = []

        for _ in range(count):
            customer = {
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "email": self.generate_unique_email(),
                "phone": self.fake.phone_number(),
                "address": self.fake.address(),
                "created_at": self.fake.date_time_between(start_date="-2y"),
                "last_login": self.fake.date_time_between(start_date="-6m"),
            }
            customers.append(customer)

        return customers

    def generate_orders(
        self, customer_ids: List[int], product_ids: List[int], count: int
    ) -> List[Dict[str, Any]]:
        """Generate order data with references to existing customers and products."""
        orders = []
        order_items = []
        status_options = ["PENDING", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"]

        for _ in range(count):
            order_date = self.fake.date_time_between(start_date="-6m")
            order = {
                "customer_id": random.choice(customer_ids),
                "order_date": order_date,
                "status": random.choice(status_options),
                "total_amount": 0,
            }
            orders.append(order)

            num_items = random.randint(1, 5)
            order_total = 0

            selected_products = random.sample(
                product_ids, min(num_items, len(product_ids))
            )

            for product_id in selected_products:
                quantity = random.randint(1, 5)
                unit_price = round(random.uniform(10, 1000), 2)
                item = {
                    "order_id": None,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": quantity * unit_price,
                }
                order_total += item["total_price"]
                order_items.append(item)

            order["total_amount"] = round(order_total, 2)

        return orders, order_items

    def insert_data(
        self,
        products: List[Dict],
        customers: List[Dict],
        orders: List[Dict],
        order_items: List[Dict],
    ) -> None:
        """Insert generated data into the database."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO products (name, description, category, price, sku, 
                                        created_at, stock_quantity)
                    VALUES %s RETURNING id
                    """,
                    [
                        (
                            p["name"],
                            p["description"],
                            p["category"],
                            p["price"],
                            p["sku"],
                            p["created_at"],
                            p["stock_quantity"],
                        )
                        for p in products
                    ],
                )

                execute_values(
                    cur,
                    """
                    INSERT INTO customers (first_name, last_name, email, phone,
                                         address, created_at, last_login)
                    VALUES %s RETURNING id
                    """,
                    [
                        (
                            c["first_name"],
                            c["last_name"],
                            c["email"],
                            c["phone"],
                            c["address"],
                            c["created_at"],
                            c["last_login"],
                        )
                        for c in customers
                    ],
                )

                execute_values(
                    cur,
                    """
                    INSERT INTO orders (customer_id, order_date, status, total_amount)
                    VALUES %s RETURNING id
                    """,
                    [
                        (
                            o["customer_id"],
                            o["order_date"],
                            o["status"],
                            o["total_amount"],
                        )
                        for o in orders
                    ],
                )

                execute_values(
                    cur,
                    """
                    INSERT INTO order_items (order_id, product_id, quantity,
                                           unit_price, total_price)
                    VALUES %s
                    """,
                    [
                        (
                            oi["order_id"],
                            oi["product_id"],
                            oi["quantity"],
                            oi["unit_price"],
                            oi["total_price"],
                        )
                        for oi in order_items
                    ],
                )

            conn.commit()
