import os
import uuid
import random
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
from multiprocessing import Process, cpu_count

# ==============================
# CONFIG
# ==============================
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "123",
}

ROWS_PER_BATCH = 10_000  # tune this (5k–50k)
BATCHES_PER_PROCESS = 100  # total rows per process = ROWS_PER_BATCH * BATCHES_PER_PROCESS

CURRENCIES = ["USD", "EUR", "GBP"]
PAYMENT_METHODS = ["card", "paypal", "apple_pay", "google_pay"]
STATUSES = ["paid", "pending", "failed", "refunded"]


# ==============================
# DATA GENERATOR
# ==============================
def generate_row():
    quantity = random.randint(1, 5)
    price = round(random.uniform(5, 500), 2)
    total = round(quantity * price, 2)

    return (
        str(uuid.uuid4()),                 # order_id ✅ FIXED
        random.randint(1, 5_000_000),
        random.randint(1, 1_000_000),
        quantity,
        price,
        total,
        random.choice(CURRENCIES),
        random.choice(PAYMENT_METHODS),
        random.choice(STATUSES),
        datetime.utcnow() - timedelta(
            seconds=random.randint(0, 60 * 60 * 24 * 365)
        ),
    )


# ==============================
# WORKER PROCESS
# ==============================
def insert_worker(worker_id: int):
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    insert_sql = """
                 INSERT INTO ecommerce_transactions (order_id,
                                                     user_id,
                                                     product_id,
                                                     quantity,
                                                     price,
                                                     total_amount,
                                                     currency,
                                                     payment_method,
                                                     transaction_status,
                                                     created_at)
                 VALUES %s \
                 """

    total_inserted = 0

    try:
        for batch in range(BATCHES_PER_PROCESS):
            rows = [generate_row() for _ in range(ROWS_PER_BATCH)]
            execute_values(cur, insert_sql, rows, page_size=ROWS_PER_BATCH)
            conn.commit()
            total_inserted += len(rows)

            print(f"[Worker {worker_id}] Inserted {total_inserted:,} rows")

    except Exception as e:
        conn.rollback()
        print(f"[Worker {worker_id}] ERROR:", e)

    finally:
        cur.close()
        conn.close()


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    workers = cpu_count()
    print(f"Starting {workers} processes")

    processes = []
    for i in range(workers):
        p = Process(target=insert_worker, args=(i,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print("🔥 Data generation complete")
