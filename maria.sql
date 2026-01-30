-- 1) Create DB
CREATE DATABASE IF NOT EXISTS insurance_pricing;
USE insurance_pricing;

-- 2) Customers table (simple)
CREATE TABLE IF NOT EXISTS customers (
  customerId        INT PRIMARY KEY,
  fullName          VARCHAR(120) NOT NULL,
  lastContractDate  DATE NOT NULL,
  currentPricePerMonth     DECIMAL(10,2) NULL,
  lastScoredAt      DATETIME NULL,
  modelVersion      VARCHAR(50) NULL
);

-- -- (Optional but nice) keep an audit trail of each scoring run + per-customer prediction
CREATE TABLE IF NOT EXISTS scoring_runs (
  runId        BIGINT PRIMARY KEY AUTO_INCREMENT,
  runTs        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modelVersion VARCHAR(50) NOT NULL,
  notes        VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS customer_predictions (
  predId       BIGINT PRIMARY KEY AUTO_INCREMENT,
  runId        BIGINT NOT NULL,
  customerId   INT NOT NULL,
  pricePerMonth DECIMAL(10,2) NOT NULL,
  scoredAt     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (runId) REFERENCES scoring_runs(runId),
  FOREIGN KEY (customerId) REFERENCES customers(customerId)
);

-- 3) Seed some mock customers with different lastContractDate values
-- Mix: some older than 11 months (eligible), some newer (not eligible)
INSERT INTO customers (customerId, fullName, lastContractDate, currentPricePerMonth, lastScoredAt, modelVersion) VALUES
(1, 'Alex Johnson',     CURDATE() - INTERVAL 13 MONTH, NULL, NULL, NULL),
(2, 'Maria Garcia',     CURDATE() - INTERVAL  3 MONTH, NULL, NULL, NULL),
(3, 'Chen Wei',         CURDATE() - INTERVAL 11 MONTH, NULL, NULL, NULL),
(4, 'Fatima Khan',      CURDATE() - INTERVAL 18 MONTH, NULL, NULL, NULL),
(5, 'Luca Rossi',       CURDATE() - INTERVAL  9 MONTH, NULL, NULL, NULL),
(6, 'Sofia Martinez',   CURDATE() - INTERVAL 12 MONTH, NULL, NULL, NULL),
(7, 'Noah Williams',    CURDATE() - INTERVAL  1 MONTH, NULL, NULL, NULL),
(8, 'Amina Diallo',     CURDATE() - INTERVAL 15 MONTH, NULL, NULL, NULL),
(9, 'Hiro Tanaka',      CURDATE() - INTERVAL 10 MONTH, NULL, NULL, NULL),
(10,'Emma Brown',       CURDATE() - INTERVAL 20 MONTH, NULL, NULL, NULL)
ON DUPLICATE KEY UPDATE
  fullName = VALUES(fullName),
  lastContractDate = VALUES(lastContractDate);
