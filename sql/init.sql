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

-- Insert sample data
INSERT INTO customers VALUES (1, 'John Doe', 'john@example.com');
INSERT INTO orders VALUES (101, 1, 'Laptop', 1200.00);