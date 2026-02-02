# End-to-End PyFlink CDC Project Setup Steps (MySQL to Elasticsearch)

This document outlines the steps taken to set up an end-to-end PyFlink CDC project that reads from MySQL (via Debezium) and writes enriched results to Elasticsearch, all within Docker containers.

## 1. Define Docker Services (`docker-compose.yml`)
- **Reason:** To run all dependencies with compatible versions:
  - **MySQL (Debezium image):** Provides binlog-enabled MySQL for CDC.
  - **Elasticsearch 7.x:** Sink for enriched order data.
  - **Flink JobManager/TaskManager:** Runs the PyFlink job.
- **Note:** The current compose file downloads required connector JARs at container startup.

## 2. Initialize MySQL Schema and Seed Data (`sql/init.sql`)
- **Reason:** Provide a source dataset for CDC:
  - `inventory.customers`
  - `inventory.orders`
- **Seed rows** are inserted so the initial snapshot produces output.

## 3. Implement the PyFlink CDC Job (`main.py`)
- **Reason:** Define the streaming pipeline:
  - **MySQL CDC sources:** `customers` and `orders` tables using `mysql-cdc`.
  - **Elasticsearch sink:** `es_sink` using `elasticsearch-7`.
  - **Join + transform:** `orders` left-joined to `customers`, producing enriched orders.

## 4. Bring Up the Stack
- **Reason:** Start all containers and let MySQL initialize the schema:
  - `docker compose up`
- **Expectations:** MySQL and Elasticsearch will be reachable on ports `3306` and `9200`.

## 5. Submit the PyFlink Job
- **Reason:** The PyFlink job is not auto-submitted by the compose file.
- **Example (inside JobManager container):**
  - `flink run -py /opt/flink/usrlib/main.py`

## 6. Verify Output in Elasticsearch
- **Reason:** Validate that the join output is written to the sink index:
  - Index: `enriched_orders`
  - Use an Elasticsearch query to confirm documents are created from the seed data.

## 7. Test CDC Changes
- **Reason:** Confirm live CDC flow:
  - Insert/update rows in `inventory.customers` or `inventory.orders`
  - Verify updated documents appear in Elasticsearch

## Optional Improvements
- Use a custom Flink image (see `sql/Dockerfile.txt`) to preinstall PyFlink and connector JARs.
- Add a `pyflink-job` service to `docker-compose.yml` to auto-submit the job.