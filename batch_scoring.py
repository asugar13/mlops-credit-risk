import os
import hashlib
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP

import mysql.connector

# Change if you want
MODEL_VERSION = os.getenv("MODEL_VERSION", "mock-renewal-v1")


def stable_price(customer_id: int, asof_date: dt.date) -> Decimal:
    """
    Deterministic pseudo-random price based on (customer_id, asof_date).
    Makes demos reproducible per day.
    """
    key = f"{customer_id}:{asof_date.isoformat()}".encode("utf-8")
    h = hashlib.sha256(key).hexdigest()
    u = int(h[:8], 16) / float(0xFFFFFFFF)  # -> [0, 1)

    # Example price range: 40..120
    price = 40 + (80 * u)
    return Decimal(price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main():
    # Expect these env vars (e.g. injected by Jenkins)
    db_host = os.environ["DB_HOST"]
    db_user = os.environ["DB_USER"]
    db_password = os.environ["DB_PASSWORD"]

    db_port = int(os.getenv("DB_PORT", "3306"))
    db_name = os.getenv("DB_NAME", "insurance_pricing")

    cnx = mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
    )
    cnx.autocommit = False

    today = dt.date.today()
    now = dt.datetime.utcnow()

    try:
        cur = cnx.cursor(dictionary=True)

        # 1) Create a scoring run (audit header)
        cur.execute(
            """
            INSERT INTO scoring_runs (modelVersion, notes)
            VALUES (%s, %s)
            """,
            (MODEL_VERSION, "Mock batch scoring for renewals (>= 11 months)"),
        )
        run_id = cur.lastrowid

        # 2) Select eligible customers
        cur.execute(
            """
            SELECT customerId, fullName, lastContractDate
            FROM customers
            WHERE lastContractDate <= (CURDATE() - INTERVAL 11 MONTH)
            """
        )
        customers = cur.fetchall()

        # 3) Generate and store predictions
        inserted = 0
        for c in customers:
            cid = int(c["customerId"])
            price = stable_price(cid, today)

            # Insert prediction row
            cur.execute(
                """
                INSERT INTO customer_predictions (runId, customerId, pricePerMonth, scoredAt)
                VALUES (%s, %s, %s, %s)
                """,
                (run_id, cid, str(price), now),
            )

            # Update "lastScoredAt" and "modelVersion" on the customer
            # (Keep currentPricePerMonth separate: you can update it later if "approved")
            cur.execute(
                """
                UPDATE customers
                SET lastScoredAt = %s,
                    modelVersion = %s
                WHERE customerId = %s
                """,
                (now, MODEL_VERSION, cid),
            )

            inserted += 1

        cnx.commit()
        print(f"Run {run_id}: inserted {inserted} prediction(s). Model={MODEL_VERSION}")

    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


if __name__ == "__main__":
    main()
