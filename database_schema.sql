-- Create database
CREATE DATABASE IF NOT EXISTS chatbot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE chatbot_db;

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(15) UNIQUE,
    email VARCHAR(255) UNIQUE,
    vehicle_model VARCHAR(100),
    vehicle_variant VARCHAR(100),
    registration_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phone (phone),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_message TEXT,
    bot_response TEXT,
    state VARCHAR(50),
    should_escalate BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Service requests table
CREATE TABLE IF NOT EXISTS service_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_id VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT,
    session_id VARCHAR(100),
    issue_type VARCHAR(50) NOT NULL,
    issue_description TEXT,
    service_type VARCHAR(50) NOT NULL,
    location_data JSON,
    safety_status VARCHAR(20),
    status VARCHAR(20) DEFAULT 'OPEN', -- OPEN, IN_PROGRESS, DISPATCHED, ON_SITE, RESOLVED, CLOSED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    INDEX idx_request_id (request_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Escalations table
CREATE TABLE IF NOT EXISTS escalations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    customer_id INT,
    reason VARCHAR(50) NOT NULL,
    collected_data JSON,
    status VARCHAR(20) DEFAULT 'OPEN', -- OPEN, IN_PROGRESS, DISPATCHED, ON_SITE, RESOLVED, CLOSED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    INDEX idx_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert sample customers for testing
INSERT INTO customers (name, phone, email, vehicle_model, vehicle_variant, registration_number) VALUES
('Test User', '9876543210', 'test@example.com', 'Maruti Swift', 'VXI', 'KA01AB1234'),
('Demo User', '9876543211', 'demo@example.com', 'Hyundai i20', 'Asta', 'KA02CD5678');   