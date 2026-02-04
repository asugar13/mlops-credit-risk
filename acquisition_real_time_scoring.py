import os
import json
import hashlib
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP

from flask import Flask, request, jsonify
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)

MODEL_VERSION = os.getenv("MODEL_VERSION", "mock-acquisition-v1")

DB_HOST = 'localhost'
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "insurance_pricing")
DB_USER = 'osbdet'
DB_PASSWORD = 'osbdet123$'


def stable_price(payload: dict, asof_date: dt.date) -> Decimal:
    """Deterministic pseudo-price based on payload + date (repeatable per day)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    key = f"{canonical}:{asof_date.isoformat()}".encode("utf-8")
    h = hashlib.sha256(key).hexdigest()
    u = int(h[:8], 16) / float(0xFFFFFFFF)
    price = 35 + (105 * u)  # range: 35..140
    return Decimal(price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_conn():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=False,
        row_factory=dict_row,
    )


@app.get("/health")
def health():
    return {"status": "ok", "modelVersion": MODEL_VERSION}


@app.post("/score-acquisition")
def score_acquisition():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    # Minimal required fields for using existing schema
    customer_id = payload.get("customerId")
    full_name = payload.get("fullName")

    if customer_id is None or full_name is None:
        return jsonify({"error": "Required fields: customerId, fullName"}), 400

    try:
        customer_id = int(customer_id)
    except Exception:
        return jsonify({"error": "customerId must be an integer"}), 400

    today = dt.date.today()
    now = dt.datetime.now(dt.timezone.utc)
    price = stable_price(payload, today)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 1) Upsert customer (acquisition/new customer)
            # lastContractDate: for new business, set to today (or quote date)
            cur.execute(
                """
                INSERT INTO customers (customerId, fullName, lastContractDate, currentPricePerMonth, lastScoredAt, modelVersion)
                VALUES (%s, %s, %s, NULL, %s, %s)
                ON CONFLICT (customerId) DO UPDATE
                SET fullName = EXCLUDED.fullName
                """,
                (customer_id, full_name, today, now, MODEL_VERSION),
            )

            # 2) Create scoring run (one per request; simplest)
            cur.execute(
                """
                INSERT INTO scoring_runs (modelVersion, notes)
                VALUES (%s, %s)
                RETURNING runId
                """,
                (MODEL_VERSION, "Real-time acquisition scoring"),
            )
            run_id = cur.fetchone()["runid"]

            # 3) Store prediction
            cur.execute(
                """
                INSERT INTO customer_predictions (runId, customerId, pricePerMonth, scoredAt)
                VALUES (%s, %s, %s, %s)
                """,
                (run_id, customer_id, price, now),
            )

        conn.commit()

        return jsonify(
            {
                "customerId": customer_id,
                "runId": run_id,
                "pricePerMonth": float(price),
                "currency": "EUR",
                "modelVersion": MODEL_VERSION,
            }
        )

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8081")), debug=True)
