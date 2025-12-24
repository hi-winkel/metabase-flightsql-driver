-- GizmoSQL initialization script with multiple schemas for testing Metabase connector

-- Create schemas
CREATE SCHEMA IF NOT EXISTS sales;
CREATE SCHEMA IF NOT EXISTS hr;
CREATE SCHEMA IF NOT EXISTS analytics;

-- =============================================================================
-- SALES SCHEMA
-- =============================================================================

-- Customers table
CREATE TABLE sales.customers (
    customer_id INTEGER PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    city VARCHAR(50),
    country VARCHAR(50),
    created_at TIMESTAMP
);

INSERT INTO sales.customers VALUES
(1, 'Alice', 'Johnson', 'alice.johnson@email.com', 'New York', 'USA', '2024-01-15 10:30:00'),
(2, 'Bob', 'Smith', 'bob.smith@email.com', 'London', 'UK', '2024-01-20 14:45:00'),
(3, 'Carlos', 'Garcia', 'carlos.garcia@email.com', 'Madrid', 'Spain', '2024-02-01 09:15:00'),
(4, 'Diana', 'Chen', 'diana.chen@email.com', 'Shanghai', 'China', '2024-02-10 16:00:00'),
(5, 'Erik', 'Johansson', 'erik.j@email.com', 'Stockholm', 'Sweden', '2024-02-15 11:30:00'),
(6, 'Fatima', 'Al-Hassan', 'fatima.ah@email.com', 'Dubai', 'UAE', '2024-03-01 08:00:00'),
(7, 'George', 'Wilson', 'george.w@email.com', 'Sydney', 'Australia', '2024-03-05 13:20:00'),
(8, 'Hannah', 'Mueller', 'hannah.m@email.com', 'Berlin', 'Germany', '2024-03-10 15:45:00');

-- Products table
CREATE TABLE sales.products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10, 2),
    stock_quantity INTEGER,
    supplier VARCHAR(100)
);

INSERT INTO sales.products VALUES
(1, 'Laptop Pro 15', 'Electronics', 1299.99, 150, 'TechCorp'),
(2, 'Wireless Mouse', 'Electronics', 29.99, 500, 'TechCorp'),
(3, 'Office Chair Deluxe', 'Furniture', 349.00, 75, 'ComfortSeating'),
(4, 'Standing Desk', 'Furniture', 599.00, 40, 'ComfortSeating'),
(5, 'Monitor 27 inch', 'Electronics', 449.99, 200, 'DisplayTech'),
(6, 'Keyboard Mechanical', 'Electronics', 149.99, 300, 'TechCorp'),
(7, 'Webcam HD', 'Electronics', 79.99, 250, 'DisplayTech'),
(8, 'Desk Lamp LED', 'Furniture', 45.00, 180, 'LightWorks'),
(9, 'Notebook Set', 'Office Supplies', 12.99, 1000, 'PaperPlus'),
(10, 'Pen Premium Pack', 'Office Supplies', 24.99, 800, 'PaperPlus');

-- Orders table
CREATE TABLE sales.orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    total_amount DECIMAL(10, 2),
    status VARCHAR(20),
    shipping_address VARCHAR(200)
);

INSERT INTO sales.orders VALUES
(1001, 1, '2024-03-01', 1329.98, 'Delivered', '123 Main St, New York, NY'),
(1002, 2, '2024-03-02', 349.00, 'Delivered', '45 Oxford St, London, UK'),
(1003, 3, '2024-03-03', 599.00, 'Shipped', 'Calle Mayor 10, Madrid, Spain'),
(1004, 4, '2024-03-05', 529.98, 'Delivered', '88 Nanjing Rd, Shanghai, China'),
(1005, 1, '2024-03-07', 149.99, 'Delivered', '123 Main St, New York, NY'),
(1006, 5, '2024-03-10', 1749.98, 'Processing', 'Kungsgatan 5, Stockholm, Sweden'),
(1007, 6, '2024-03-12', 79.99, 'Shipped', 'Sheikh Zayed Rd, Dubai, UAE'),
(1008, 7, '2024-03-15', 944.99, 'Delivered', '200 George St, Sydney, Australia'),
(1009, 2, '2024-03-18', 37.98, 'Delivered', '45 Oxford St, London, UK'),
(1010, 8, '2024-03-20', 1898.98, 'Processing', 'Friedrichstr 100, Berlin, Germany');

-- Order items table
CREATE TABLE sales.order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    unit_price DECIMAL(10, 2)
);

INSERT INTO sales.order_items VALUES
(1, 1001, 1, 1, 1299.99),
(2, 1001, 2, 1, 29.99),
(3, 1002, 3, 1, 349.00),
(4, 1003, 4, 1, 599.00),
(5, 1004, 5, 1, 449.99),
(6, 1004, 7, 1, 79.99),
(7, 1005, 6, 1, 149.99),
(8, 1006, 1, 1, 1299.99),
(9, 1006, 5, 1, 449.99),
(10, 1007, 7, 1, 79.99),
(11, 1008, 5, 1, 449.99),
(12, 1008, 4, 1, 599.00),
(13, 1009, 9, 2, 12.99),
(14, 1009, 10, 1, 24.99),
(15, 1010, 1, 1, 1299.99),
(16, 1010, 4, 1, 599.00);

-- =============================================================================
-- HR SCHEMA
-- =============================================================================

-- Departments table
CREATE TABLE hr.departments (
    department_id INTEGER PRIMARY KEY,
    department_name VARCHAR(50),
    location VARCHAR(100),
    budget DECIMAL(12, 2)
);

INSERT INTO hr.departments VALUES
(1, 'Engineering', 'Building A, Floor 3', 2500000.00),
(2, 'Sales', 'Building B, Floor 1', 1800000.00),
(3, 'Marketing', 'Building B, Floor 2', 1200000.00),
(4, 'Human Resources', 'Building A, Floor 1', 800000.00),
(5, 'Finance', 'Building C, Floor 1', 950000.00),
(6, 'Operations', 'Building D, Floor 1', 1500000.00);

-- Employees table
CREATE TABLE hr.employees (
    employee_id INTEGER PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    department_id INTEGER,
    job_title VARCHAR(100),
    hire_date DATE,
    salary DECIMAL(10, 2),
    manager_id INTEGER
);

INSERT INTO hr.employees VALUES
(1, 'John', 'Davis', 'john.davis@company.com', 1, 'VP of Engineering', '2020-01-15', 180000.00, NULL),
(2, 'Sarah', 'Miller', 'sarah.miller@company.com', 1, 'Senior Software Engineer', '2021-03-01', 145000.00, 1),
(3, 'Michael', 'Brown', 'michael.brown@company.com', 1, 'Software Engineer', '2022-06-15', 110000.00, 2),
(4, 'Emily', 'Taylor', 'emily.taylor@company.com', 1, 'Software Engineer', '2023-01-10', 105000.00, 2),
(5, 'James', 'Anderson', 'james.anderson@company.com', 2, 'Sales Director', '2020-05-20', 160000.00, NULL),
(6, 'Jennifer', 'Thomas', 'jennifer.thomas@company.com', 2, 'Account Executive', '2021-08-01', 95000.00, 5),
(7, 'Robert', 'Jackson', 'robert.jackson@company.com', 2, 'Account Executive', '2022-02-14', 90000.00, 5),
(8, 'Lisa', 'White', 'lisa.white@company.com', 3, 'Marketing Manager', '2021-01-05', 120000.00, NULL),
(9, 'David', 'Harris', 'david.harris@company.com', 3, 'Content Specialist', '2022-09-01', 75000.00, 8),
(10, 'Amanda', 'Martin', 'amanda.martin@company.com', 4, 'HR Director', '2019-11-01', 140000.00, NULL),
(11, 'Kevin', 'Lee', 'kevin.lee@company.com', 4, 'HR Specialist', '2023-02-20', 65000.00, 10),
(12, 'Rachel', 'Clark', 'rachel.clark@company.com', 5, 'Finance Manager', '2020-07-15', 130000.00, NULL),
(13, 'Steven', 'Lewis', 'steven.lewis@company.com', 5, 'Financial Analyst', '2022-04-01', 85000.00, 12),
(14, 'Michelle', 'Walker', 'michelle.walker@company.com', 6, 'Operations Manager', '2021-06-01', 125000.00, NULL),
(15, 'Daniel', 'Hall', 'daniel.hall@company.com', 6, 'Operations Coordinator', '2023-03-15', 60000.00, 14);

-- Time off requests table
CREATE TABLE hr.time_off_requests (
    request_id INTEGER PRIMARY KEY,
    employee_id INTEGER,
    request_type VARCHAR(30),
    start_date DATE,
    end_date DATE,
    status VARCHAR(20),
    approved_by INTEGER
);

INSERT INTO hr.time_off_requests VALUES
(1, 3, 'Vacation', '2024-04-01', '2024-04-05', 'Approved', 2),
(2, 6, 'Sick Leave', '2024-03-15', '2024-03-16', 'Approved', 5),
(3, 9, 'Vacation', '2024-05-10', '2024-05-17', 'Pending', NULL),
(4, 4, 'Personal', '2024-03-20', '2024-03-20', 'Approved', 2),
(5, 11, 'Vacation', '2024-06-01', '2024-06-10', 'Pending', NULL),
(6, 7, 'Sick Leave', '2024-03-22', '2024-03-23', 'Approved', 5),
(7, 13, 'Vacation', '2024-04-15', '2024-04-19', 'Approved', 12),
(8, 15, 'Personal', '2024-03-25', '2024-03-25', 'Approved', 14);

-- =============================================================================
-- ANALYTICS SCHEMA
-- =============================================================================

-- Website events table
CREATE TABLE analytics.website_events (
    event_id INTEGER PRIMARY KEY,
    session_id VARCHAR(50),
    user_id INTEGER,
    event_type VARCHAR(30),
    page_url VARCHAR(200),
    event_timestamp TIMESTAMP,
    device_type VARCHAR(20),
    browser VARCHAR(30)
);

INSERT INTO analytics.website_events VALUES
(1, 'sess_001', 1, 'page_view', '/home', '2024-03-20 10:00:00', 'Desktop', 'Chrome'),
(2, 'sess_001', 1, 'page_view', '/products', '2024-03-20 10:02:15', 'Desktop', 'Chrome'),
(3, 'sess_001', 1, 'add_to_cart', '/products/laptop', '2024-03-20 10:05:30', 'Desktop', 'Chrome'),
(4, 'sess_001', 1, 'purchase', '/checkout', '2024-03-20 10:10:00', 'Desktop', 'Chrome'),
(5, 'sess_002', 2, 'page_view', '/home', '2024-03-20 11:30:00', 'Mobile', 'Safari'),
(6, 'sess_002', 2, 'page_view', '/products', '2024-03-20 11:32:00', 'Mobile', 'Safari'),
(7, 'sess_003', NULL, 'page_view', '/home', '2024-03-20 12:00:00', 'Desktop', 'Firefox'),
(8, 'sess_003', NULL, 'page_view', '/about', '2024-03-20 12:01:30', 'Desktop', 'Firefox'),
(9, 'sess_004', 3, 'page_view', '/home', '2024-03-20 14:00:00', 'Tablet', 'Chrome'),
(10, 'sess_004', 3, 'search', '/search?q=desk', '2024-03-20 14:02:00', 'Tablet', 'Chrome'),
(11, 'sess_004', 3, 'page_view', '/products/standing-desk', '2024-03-20 14:03:30', 'Tablet', 'Chrome'),
(12, 'sess_005', 4, 'page_view', '/home', '2024-03-20 15:00:00', 'Desktop', 'Edge'),
(13, 'sess_005', 4, 'page_view', '/products', '2024-03-20 15:01:00', 'Desktop', 'Edge'),
(14, 'sess_005', 4, 'add_to_cart', '/products/monitor', '2024-03-20 15:05:00', 'Desktop', 'Edge'),
(15, 'sess_005', 4, 'cart_abandon', '/cart', '2024-03-20 15:10:00', 'Desktop', 'Edge');

-- Daily metrics table
CREATE TABLE analytics.daily_metrics (
    metric_date DATE PRIMARY KEY,
    total_visitors INTEGER,
    unique_visitors INTEGER,
    page_views INTEGER,
    avg_session_duration_seconds INTEGER,
    bounce_rate DECIMAL(5, 2),
    conversion_rate DECIMAL(5, 2),
    revenue DECIMAL(12, 2)
);

INSERT INTO analytics.daily_metrics VALUES
('2024-03-01', 1250, 980, 4500, 185, 42.50, 3.20, 15420.50),
('2024-03-02', 1180, 920, 4200, 178, 44.00, 2.90, 12350.00),
('2024-03-03', 1320, 1050, 5100, 195, 40.20, 3.50, 18750.25),
('2024-03-04', 1150, 890, 4000, 165, 46.00, 2.80, 11200.00),
('2024-03-05', 1400, 1120, 5500, 210, 38.50, 3.80, 22100.75),
('2024-03-06', 1280, 1000, 4800, 190, 41.00, 3.40, 17500.00),
('2024-03-07', 1350, 1080, 5200, 200, 39.80, 3.60, 19800.50),
('2024-03-08', 980, 750, 3500, 155, 48.00, 2.50, 8500.00),
('2024-03-09', 920, 700, 3200, 145, 50.00, 2.30, 7200.25),
('2024-03-10', 1420, 1150, 5600, 215, 37.50, 3.90, 24500.00),
('2024-03-11', 1380, 1100, 5400, 205, 38.80, 3.70, 21200.50),
('2024-03-12', 1450, 1180, 5800, 220, 36.50, 4.00, 26000.00),
('2024-03-13', 1300, 1020, 4900, 192, 40.50, 3.45, 18100.25),
('2024-03-14', 1280, 1010, 4850, 188, 41.20, 3.35, 17200.00),
('2024-03-15', 1100, 850, 4000, 170, 45.00, 2.95, 13500.75);

-- Campaign performance table
CREATE TABLE analytics.campaign_performance (
    campaign_id INTEGER PRIMARY KEY,
    campaign_name VARCHAR(100),
    channel VARCHAR(50),
    start_date DATE,
    end_date DATE,
    budget DECIMAL(10, 2),
    spend DECIMAL(10, 2),
    impressions INTEGER,
    clicks INTEGER,
    conversions INTEGER,
    revenue DECIMAL(12, 2)
);

INSERT INTO analytics.campaign_performance VALUES
(1, 'Spring Sale 2024', 'Google Ads', '2024-03-01', '2024-03-15', 5000.00, 4850.00, 250000, 12500, 375, 45000.00),
(2, 'Product Launch - Laptop Pro', 'Facebook', '2024-03-01', '2024-03-31', 8000.00, 6200.00, 180000, 9000, 180, 52000.00),
(3, 'Email Newsletter March', 'Email', '2024-03-05', '2024-03-05', 500.00, 500.00, 45000, 6750, 540, 28500.00),
(4, 'Retargeting Campaign Q1', 'Google Ads', '2024-01-01', '2024-03-31', 3000.00, 2800.00, 120000, 4800, 192, 25600.00),
(5, 'LinkedIn B2B Outreach', 'LinkedIn', '2024-03-10', '2024-03-31', 4000.00, 2100.00, 80000, 2400, 48, 19200.00),
(6, 'Instagram Brand Awareness', 'Instagram', '2024-03-01', '2024-03-31', 3500.00, 3200.00, 200000, 8000, 120, 14400.00);

-- =============================================================================
-- VIEWS FOR TESTING
-- =============================================================================

-- Sales summary view
CREATE VIEW sales.customer_order_summary AS
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.country,
    COUNT(o.order_id) AS total_orders,
    SUM(o.total_amount) AS total_spent
FROM sales.customers c
LEFT JOIN sales.orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.country;

-- HR department summary view
CREATE VIEW hr.department_summary AS
SELECT
    d.department_id,
    d.department_name,
    COUNT(e.employee_id) AS employee_count,
    AVG(e.salary) AS avg_salary,
    d.budget
FROM hr.departments d
LEFT JOIN hr.employees e ON d.department_id = e.department_id
GROUP BY d.department_id, d.department_name, d.budget;

-- Analytics conversion funnel view
CREATE VIEW analytics.conversion_funnel AS
SELECT
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT session_id) AS unique_sessions
FROM analytics.website_events
GROUP BY event_type;
