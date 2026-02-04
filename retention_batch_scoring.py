import os
import hashlib
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP

import psycopg
from psycopg.rows import dict_row

MODEL_VERSION = os.getenv("MODEL_VERSION", "mock-renewal-v1")


def stable_price(customer_id: int, asof_date: dt.date) -> Decimal:
    key = f"{customer_id}:{asof_date.isoformat()}".encode("utf-8")
    h = hashlib.sha256(key).hexdigest()
    u = int(h[:8], 16) / float(0xFFFFFFFF)  # [0, 1)
    price = 40 + (80 * u)                   # 40..120
    return Decimal(price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main() -> None:
    db_host = os.environ["DB_HOST"]
    db_user = os.environ["DB_USER"]
    db_password = os.environ["DB_PASSWORD"]
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_name = os.getenv("DB_NAME", "insurance_pricing")

    conn = psycopg.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        dbname=db_name,
        autocommit=False,
        row_factory=dict_row,
    )

    today = dt.date.today()
    now = dt.datetime.now(dt.timezone.utc)

    try:
        with conn.cursor() as cur:
            # scoring run header
            cur.execute(
                """
                INSERT INTO scoring_runs (modelVersion, notes)
                VALUES (%s, %s)
                RETURNING runId
                """,
                (MODEL_VERSION, "Mock batch scoring for renewals (>= 11 months)"),
            )
            run_id = cur.fetchone()["runid"]

            # eligible customers
            cur.execute(
                """
                SELECT customerId, fullName, lastContractDate
                FROM customers
                WHERE lastContractDate <= (CURRENT_DATE - INTERVAL '11 months')
                ORDER BY customerId
                """
            )
            customers = cur.fetchall()

            inserted = 0
            for c in customers:
                cid = int(c["customerid"])
                price = stable_price(cid, today)

                cur.execute(
                    """
                    INSERT INTO customer_predictions (runId, customerId, pricePerMonth, scoredAt)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (run_id, cid, price, now),
                )

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

        conn.commit()
        print(f"Run {run_id}: inserted {inserted} prediction(s). Model={MODEL_VERSION}")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
