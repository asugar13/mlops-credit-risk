CREATE DATABASE insurance_pricing;

\c insurance_pricing;

CREATE TABLE IF NOT EXISTS customers (
  customerId       INT PRIMARY KEY,
  fullName         VARCHAR(120) NOT NULL,
  lastContractDate DATE,
  currentPricePerMonth NUMERIC(10,2) NULL,
  lastScoredAt     TIMESTAMPTZ NULL,
  modelVersion     VARCHAR(50) NULL
);

CREATE TABLE IF NOT EXISTS scoring_runs (
  runId        BIGSERIAL PRIMARY KEY,
  runTs        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  modelVersion VARCHAR(50) NOT NULL,
  notes        VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS customer_predictions (
  predId       BIGSERIAL PRIMARY KEY,
  runId        BIGINT NOT NULL REFERENCES scoring_runs(runId),
  customerId   INT NOT NULL REFERENCES customers(customerId),
  pricePerMonth NUMERIC(10,2) NOT NULL,
  scoredAt     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO customers (customerId, fullName, lastContractDate)
VALUES
(1, 'Alex Johnson',   CURRENT_DATE - INTERVAL '11 months'),
(2, 'Maria Garcia',   CURRENT_DATE - INTERVAL '3 months'),
(3, 'Chen Wei',       CURRENT_DATE - INTERVAL '11 months'),
(4, 'Fatima Khan',    CURRENT_DATE - INTERVAL '10 months'),
(5, 'Luca Rossi',     CURRENT_DATE - INTERVAL '9 months'),
(6, 'Sofia Martinez', CURRENT_DATE - INTERVAL '8 months'),
(7, 'Noah Williams',  CURRENT_DATE - INTERVAL '1 month'),
(8, 'Amina Diallo',   CURRENT_DATE - INTERVAL '7 months'),
(9, 'Hiro Tanaka',    CURRENT_DATE - INTERVAL '10 months'),
(10,'Emma Brown',     CURRENT_DATE - INTERVAL '9 months'),
(11,'Oliver Davis',   NULL),


ON CONFLICT (customerId) DO UPDATE
SET fullName = EXCLUDED.fullName,
    lastContractDate = EXCLUDED.lastContractDate;
