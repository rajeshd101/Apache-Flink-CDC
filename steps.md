# End-to-End PyFlink CDC Project Setup Steps (MySQL to Elasticsearch)

This document outlines the steps taken to set up an end-to-end PyFlink CDC project that reads from MySQL (via Debezium) and writes enriched results to Elasticsearch, all within Docker containers.

## 1. Define Docker Services (`docker-compose.yml`)
- **Reason:** To run all dependencies with compatible versions:
  - **MySQL (Debezium image):** Provides binlog-enabled MySQL for CDC.
  - **Elasticsearch 7.x:** Sink for enriched order data.
  - **Flink JobManager/TaskManager:** Runs the PyFlink job.
- **Compose change:** Flink services are built from a custom image (`sql/Dockerfile`) that already includes PyFlink and connector JARs.
```yaml
services:
  jobmanager:
    build:
      context: ./sql
      dockerfile: Dockerfile
    ports:
      - "8081:8081"
    command: jobmanager
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
    volumes:
      - .:/opt/flink/usrlib

  taskmanager:
    build:
      context: ./sql
      dockerfile: Dockerfile
    depends_on:
      - jobmanager
    command: taskmanager
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
        taskmanager.numberOfTaskSlots: 2
    volumes:
      - .:/opt/flink/usrlib
```

## 2. Initialize MySQL Schema and Seed Data (`sql/init.sql`)
- **Reason:** Provide a source dataset for CDC:
  - `inventory.customers`
  - `inventory.orders`
- **Seed rows** are inserted so the initial snapshot produces output.
```sql
CREATE DATABASE inventory;
USE inventory;

CREATE TABLE customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    email VARCHAR(255)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    product VARCHAR(255),
    amount DECIMAL(10, 2)
);

INSERT INTO customers VALUES (1, 'John Doe', 'john@example.com');
INSERT INTO orders VALUES (101, 1, 'Laptop', 1200.00);
```

## 3. Implement the PyFlink CDC Job (`main.py`)
- **Reason:** Define the streaming pipeline:
  - **MySQL CDC sources:** `customers` and `orders` tables using `mysql-cdc`.
  - **Elasticsearch sink:** `es_sink` using `elasticsearch-7`.
  - **Join + transform:** `orders` left-joined to `customers`, producing enriched orders.
```python
t_env.execute_sql("""
    CREATE TABLE customers (
        id INT PRIMARY KEY NOT ENFORCED,
        name STRING,
        email STRING
    ) WITH (
        'connector' = 'mysql-cdc',
        'hostname' = 'mysql',
        'port' = '3306',
        'username' = 'root',
        'password' = 'debezium',
        'database-name' = 'inventory',
        'table-name' = 'customers'
    )
""")

t_env.execute_sql("""
    CREATE TABLE orders (
        order_id INT PRIMARY KEY NOT ENFORCED,
        customer_id INT,
        product STRING,
        amount DECIMAL(10, 2)
    ) WITH (
        'connector' = 'mysql-cdc',
        'hostname' = 'mysql',
        'port' = '3306',
        'username' = 'root',
        'password' = 'debezium',
        'database-name' = 'inventory',
        'table-name' = 'orders'
    )
""")

t_env.execute_sql("""
    CREATE TABLE es_sink (
        order_id INT PRIMARY KEY NOT ENFORCED,
        customer_name STRING,
        product STRING,
        total_amount DECIMAL(10, 2)
    ) WITH (
        'connector' = 'elasticsearch-7',
        'hosts' = 'http://elasticsearch:9200',
        'index' = 'enriched_orders'
    )
""")

t_env.execute_sql("""
    INSERT INTO es_sink
    SELECT o.order_id, c.name, o.product, o.amount
    FROM orders o
    LEFT JOIN customers c ON o.customer_id = c.id
""")
```

## 4. Bring Up the Stack
- **Reason:** Start all containers and let MySQL initialize the schema:
  - Build and run:
```bash
docker compose up --build
```
- **Expectations:** MySQL and Elasticsearch will be reachable on ports `3306` and `9200`.

## 5. Submit the PyFlink Job
Run this command in your terminal to start the data synchronization:
```powershell
docker exec -it apache-flink-cdc-jobmanager-1 flink run -py /opt/flink/usrlib/main.py
```

## 6. Verify Output in Elasticsearch
- **Reason:** Validate that the join output is written to the sink index:
  - Index: `enriched_orders`
  - Use an Elasticsearch query to confirm documents are created from the seed data.
```bash
curl -s http://localhost:9200/enriched_orders/_search?pretty
```

## 7. Test CDC Changes
- **Reason:** Confirm live CDC flow:
  - Insert/update rows in `inventory.customers` or `inventory.orders`
  - Verify updated documents appear in Elasticsearch
```bash
docker exec -it apache-flink-cdc-mysql-1 mysql -uroot -pdebezium -e "USE inventory; INSERT INTO orders(customer_id, product, amount) VALUES (1, 'Mouse', 25.50);"
```

## 8. Verify the Pipeline
Once the job is running, verify that data is moving from MySQL to Elasticsearch.

### 8.1 Check MySQL CDC Status
You can check if Flink is reading the MySQL binary logs by looking at the TaskManager logs:
```bash
docker logs apache-flink-cdc-taskmanager-1
```

### 8.2 Add Data to MySQL
Open a MySQL shell and add a new record to see the real-time update:
```bash
docker exec -it apache-flink-cdc-mysql-1 mysql -u root -pdebezium inventory
```
```sql
INSERT INTO customers (name, email) VALUES ('Jane Smith', 'jane@example.com');
INSERT INTO orders (customer_id, product, amount) VALUES (2, 'Smartphone', 800.00);
```

### 8.3 Check Elasticsearch
Verify that the joined data (Customer Name + Order Details) appears as a JSON document in Elasticsearch:
```bash
curl -X GET "localhost:9200/enriched_orders/_search?pretty"
```

## Architecture Recap
- **Flink Source:** Uses the `mysql-cdc` connector to act as a MySQL replica, reading row-level changes from the binlog.
- **Join Operator:** The PyFlink Table API performs a stateful join, attaching customer data to incoming orders.
- **Elasticsearch Sink:** Converts the Flink stream into REST calls that index JSON documents.

## Optional Automation
Would you like me to help you write a Python script to automate verification by generating random orders and checking the Elasticsearch count?



-- Rajesh Daggupati