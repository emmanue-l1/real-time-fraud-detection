CREATE TABLE IF NOT EXISTS fraud_events (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    location VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    anomaly_score NUMERIC(5, 4) NOT NULL,
    is_anomaly BOOLEAN NOT NULL,
    llm_explanation TEXT
);
