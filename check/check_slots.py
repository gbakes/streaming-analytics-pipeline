#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from dotenv import load_dotenv


def check_replication_slots():
    """Check PostgreSQL replication slots"""
    load_dotenv()

    conn = psycopg2.connect(
        host="localhost",
        database=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres123"),
        port=os.getenv("POSTGRES_PORT", "5432"),
    )

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        print("\n=== Replication Slots ===")
        cur.execute(
            """
            SELECT * FROM pg_replication_slots;
        """
        )
        slots = cur.fetchall()
        for slot in slots:
            print(json.dumps(slot, indent=2, default=str))

        print("\n=== Table Change Tracking ===")
        tables = ["customers", "products", "orders", "order_items"]
        for table in tables:
            cur.execute(
                f"""
                SELECT COUNT(*) as total,
                       MIN(created_at) as earliest,
                       MAX(created_at) as latest
                FROM {table};
            """
            )
            stats = cur.fetchone()
            print(f"\n{table.upper()}:")
            print(json.dumps(stats, indent=2, default=str))


if __name__ == "__main__":
    check_replication_slots()
