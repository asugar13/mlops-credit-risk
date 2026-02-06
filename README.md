# MLOps Demo — Insurance Pricing (Batch Renewals + Real time quotations)

This repo is a **simple MLOps demonstration** for an auto-insurance pricing use case:

- **Batch scoring for renewals** runs on a **Jenkins cron schedule**
- A **Postgres** database stores:
  - Customers and renewal dates
  - Scoring runs (audit)
  - Predictions (per-customer output)

> The “model” can be a placeholder (e.g., deterministic pseudo-random premium) for demonstration purposes.

---

## Architecture (high level)

- **Postgres (Docker container)**: stores customers + predictions  
- **Jenkins (Docker container)**: runs the batch pipeline on a schedule  
- **Docker network (`mlops-net`)**: allows Jenkins to connect to Postgres by hostname (`postgres`)

---

## Repo contents (typical)

- `init_postgres.sql` — creates tables + seeds mock customers
- `retention_batch_scoring.py` — selects renewal-eligible customers and writes predictions
- `requirements.txt` — Python dependencies (e.g., `psycopg[binary]`)
- `Jenkinsfile` — pipeline-as-code for scheduled batch scoring
- `Dockerfile` — custom Jenkins image with Python installed
- `acquisition_real_time_scoring.py` - Flask server for real time scoring
- `acquisition_real_time_requirements.txt` - Flask server dependencies

---

## Prerequisites

- Docker Desktop installed and running
- Ports available:
  - `5432` for Postgres
  - `8080` for Jenkins
  - `50000` for Jenkins agents (optional)

---

## 1 - Create the Docker network

```bash
docker network create mlops-net
```

## 2 — Start Postgres

```bash
docker run -d --name postgres \
  --network mlops-net \
  -e POSTGRES_USER=osbdet \
  -e POSTGRES_PASSWORD='osbdet123$' \
  -e POSTGRES_DB=insurance_pricing \
  -p 5432:5432 \
  postgres:15
  ```

## 3 — Load schema + seed data
```bash
docker exec -i postgres psql -U osbdet -d insurance_pricing < init_postgres.sql
```

## 4 — Build Jenkins (with Python)
```bash
docker stop jenkins
docker rm jenkins
docker build -t jenkins:lts .
```

## 5 — Run Jenkins
```bash
docker run -d --name jenkins \
  --network mlops-net \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

Get the initial admin password:
```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Open Jenkins: http://localhost:8080

## 6 — Create the Jenkins Pipeline job (from Git)

In Jenkins UI:

New Item → Pipeline

Definition: Pipeline script from SCM

SCM: Git

Repository URL: https://github.com/asugar13/mlops-credit-risk

Script Path: Jenkinsfile

Make sure your Jenkinsfile uses the Docker hostname for Postgres:

- DB_HOST=postgres

- DB_PORT=5432

- DB_NAME=insurance_pricing

- DB_USER=osbdet

- DB_PASSWORD=osbdet123$

## 7 — Run and verify batch scoring
Run Build Now in Jenkins (or wait for the cron schedule).

Verify results in Postgres:

```bash
docker exec -it postgres psql -U osbdet -d insurance_pricing
```

Example queries:
```bash
SELECT * FROM scoring_runs;
```
## 8 — Real-time scoring API (Flask) + how to test it

This repo can also include a simple Flask API to demonstrate **real-time scoring for new quotations**.  
The endpoint generates a deterministic pseudo-premium and stores the prediction in Postgres.

---

### Run the server locally

Create/activate a venv and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
pip install flask psycopg[binary]
```

Run the server (file name: `acquisition_real_time_scoring.py`):

```bash
python3 acquisition_real_time_scoring.py
```

Server runs on:

http://localhost:8081

### Test the API
Score a new customer (quotation):

```bash
curl -X POST http://localhost:8081/score-acquisition \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": 2,
    "fullName": "Maria Garcias",
  }'
```

and verify the prediction was stored in Postgres