from pyflink.table import EnvironmentSettings, TableEnvironment

def run_cdc_job():
    # 1. Initialize Table Environment
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = TableEnvironment.create(settings)

    # 2. Define MySQL Source Table 1 (Customers)
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

    # 3. Define MySQL Source Table 2 (Orders)
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

    # 4. Define Elasticsearch Sink Table
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

    # 5. Join Operator & Transformation
    # This matches the "Join Operator" in your diagram
    t_env.execute_sql("""
        INSERT INTO es_sink
        SELECT o.order_id, c.name, o.product, o.amount
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
    """)

if __name__ == '__main__':
    run_cdc_job()