#!/usr/bin/env python3
import os
from itertools import zip_longest

import psycopg2
from data_generator import DataGenerator
from dotenv import load_dotenv
from psycopg2.extras import execute_values


def main():
    load_dotenv()

    db_config = {
        "host": "localhost",
        "database": os.getenv("POSTGRES_DB", "postgres"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres123"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }

    generator = DataGenerator(db_config)

    try:
        print("Connecting to database...")
        conn = generator.connect()
        cur = conn.cursor()

        # print("Clearing existing data...")
        # cur.execute("""
        #     TRUNCATE TABLE order_items CASCADE;
        #     TRUNCATE TABLE orders CASCADE;
        #     TRUNCATE TABLE customers CASCADE;
        #     TRUNCATE TABLE products CASCADE;
        # """)
        # conn.commit()

        print("Generating products...")
        products = generator.generate_products(100)
        print(f"Generated {len(products)} products")

        execute_values(
            cur,
            """
            INSERT INTO products 
                (name, description, category, price, sku, created_at, stock_quantity)
            VALUES %s 
            RETURNING id
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
        product_ids = [row[0] for row in cur.fetchall()]
        print(f"Inserted {len(product_ids)} products")

        print("Generating customers...")
        customers = generator.generate_customers(1000)
        print(f"Generated {len(customers)} customers")

        execute_values(
            cur,
            """
            INSERT INTO customers 
                (first_name, last_name, email, phone, address, created_at, last_login)
            VALUES %s 
            RETURNING id
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
        customer_ids = [row[0] for row in cur.fetchall()]
        print(f"Inserted {len(customer_ids)} customers")

        print("Generating orders...")
        orders, order_items = generator.generate_orders(customer_ids, product_ids, 500)
        print(f"Generated {len(orders)} orders with {len(order_items)} order items")

        order_tuples = [
            (o["customer_id"], o["order_date"], o["status"], o["total_amount"])
            for o in orders
        ]

        execute_values(
            cur,
            """
            INSERT INTO orders 
                (customer_id, order_date, status, total_amount)
            VALUES %s 
            RETURNING id
            """,
            order_tuples,
        )
        order_ids = [row[0] for row in cur.fetchall()]

        items_per_order = len(order_items) // len(orders)
        order_items_list = []

        for order_idx, order_id in enumerate(order_ids):
            start_idx = order_idx * items_per_order
            end_idx = start_idx + items_per_order
            order_items_subset = order_items[start_idx:end_idx]

            for item in order_items_subset:
                order_items_list.append(
                    (
                        order_id,
                        item["product_id"],
                        item["quantity"],
                        item["unit_price"],
                        item["total_price"],
                    )
                )

        execute_values(
            cur,
            """
            INSERT INTO order_items 
                (order_id, product_id, quantity, unit_price, total_price)
            VALUES %s
            """,
            order_items_list,
        )

        conn.commit()
        print("Successfully inserted all test data!")

        print("\nData Summary:")
        cur.execute("SELECT COUNT(*) FROM products")
        print(f"Products: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM customers")
        print(f"Customers: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM orders")
        print(f"Orders: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM order_items")
        print(f"Order Items: {cur.fetchone()[0]}")

        print("\nSample Order:")
        cur.execute(
            """
            SELECT o.id, o.order_date, o.status, o.total_amount, 
                   COUNT(oi.id) as item_count,
                   SUM(oi.total_price) as items_total
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            GROUP BY o.id, o.order_date, o.status, o.total_amount
            LIMIT 1
        """
        )
        sample_order = cur.fetchone()
        if sample_order:
            print(f"Order ID: {sample_order[0]}")
            print(f"Date: {sample_order[1]}")
            print(f"Status: {sample_order[2]}")
            print(f"Total Amount: ${sample_order[3]:.2f}")
            print(f"Number of Items: {sample_order[4]}")
            print(f"Items Total: ${sample_order[5]:.2f}")

    except Exception as e:
        print(f"Error generating data: {str(e)}")
        import traceback

        print(traceback.format_exc())
        if "conn" in locals():
            conn.rollback()
    finally:
        if "cur" in locals():
            cur.close()
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
