import mysql.connector
import requests
import time
import random

# Configuration
MYSQL_CONFIG = {
    'user': 'root',
    'password': 'debezium',
    'host': '127.0.0.1',
    'database': 'inventory'
}
ES_URL = "http://localhost:9200/enriched_orders/_search"

def insert_random_data():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # 1. Insert a new customer
        name = f"User_{random.randint(100, 999)}"
        email = f"{name.lower()}@example.com"
        cursor.execute("INSERT INTO customers (name, email) VALUES (%s, %s)", (name, email))
        customer_id = cursor.lastrowid
        print(f"INSERT INTO customers (name, email) VALUES ({name}, {email})")
        # 2. Insert a corresponding order
        product = random.choice(['Monitor', 'Keyboard', 'Mouse', 'Desk', 'Chair'])
        amount = round(random.uniform(20.0, 500.0), 2)
        cursor.execute(
            "INSERT INTO orders (customer_id, product, amount) VALUES (%s, %s, %s)",
            (customer_id, product, amount)
        )
        
        conn.commit()
        print(f"Successfully inserted: Customer {name} bought a {product} for ${amount}")
        cursor.close()
        conn.close()
        return name
    except Exception as e:
        print(f"MySQL Error: {e}")
        return None

def verify_elasticsearch(expected_name):
    print(f"Waiting for Flink to process CDC events...")
    time.sleep(5)  # Give Flink time to process
    
    try:
        response = requests.get(ES_URL)
        data = response.json()
        hits = data.get('hits', {}).get('hits', [])
        
        # Check if the most recent record matches our inserted name
        found = any(hit['_source']['customer_name'] == expected_name for hit in hits)
        
        if found:
            print(f"Verified! Record for '{expected_name}' found in Elasticsearch.")
        else:
            print(f"Verification Failed. Record for '{expected_name}' not found yet.")
    except Exception as e:
        print(f"ES Error: {e}")

if __name__ == "__main__":
    new_user = insert_random_data()
    if new_user:
        verify_elasticsearch(new_user)