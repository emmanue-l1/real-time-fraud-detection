# real-time-fraud-detection

Here is a comprehensive summary of the entire Real-Time Anomaly & Fraud Detection Pipeline project, capturing the core architecture alongside all incremental modifications, bug fixes, and version updates made up to this point.

## Project Overview & Tech Stack
This project is a containerized, event-driven streaming system that generates synthetic financial transactions, streams them through a message queue, evaluates them for potential fraud using a Scikit-Learn machine learning model, generates natural-language risk summaries for anomalies, and persists results into a relational database for live monitoring.

1. Message Broker: Apache Kafka 4.3.1 (KRaft Mode)

2. ML Inference Service: FastAPI + Scikit-Learn (Isolation Forest)

3. LLM Engine: OpenAI API (gpt-3.5-turbo)

4. Database & Visuals: PostgreSQL 17.7 + Streamlit Dashboard

5. Container Environment: Docker & Docker Compose on Python 3.12-slim

## End-to-End Data Lifecycle
1. Generation: producer.py creates continuous JSON payload events representing normal vs. high-risk transactions.

2. Streaming: Messages stream into Kafka via internal topic routing (kafka:29092).

3. Consumption & Health Checks: consumer.py reads events from Kafka. It validates connectivity with downstream services before making HTTP REST scoring requests to ml_service.

4. Machine Learning Scoring: ml_service runs the incoming feature vector (amount, location_code, device_code) through an Isolation Forest model, assigning an anomaly flag (is_anomaly) and a standardized anomaly_score.

5. AI Summarization: If a transaction is flagged as an anomaly (is_anomaly == True), consumer.py sends event context to the OpenAI API to receive a 2-sentence plain-English explanation.

6. Storage & Dashboard: Events, scores, and generated summaries are written to the fraud_events table in PostgreSQL 17.7. The Streamlit dashboard auto-queries Postgres to render live scatter plots, anomaly distribution histograms, and actionable risk reports.

## Key Modifications & Enhancements Applied
1. Modernized Base Images & Architecture Simplification
- ZooKeeper Elimination: Switched from Confluent images to the official apache/kafka:4.3.1 running in native KRaft consensus mode. This removed ZooKeeper completely, cutting infrastructure overhead.
- Modernized Runtimes: Updated database to PostgreSQL 17.7-alpine and standard base images for microservices to Python 3.12-slim.

2. Robust Consumer Startup & Network Resiliency
- Health Wait-Loops (wait_for_ml_service): Added explicit HTTP polling in consumer.py before stream loops begin. This prevents ConnectionRefused errors caused when Kafka delivers events before FastAPI finishes starting up.
- Database Reconnection Logic: Wrapped PostgreSQL writes in try/except psycopg2.OperationalError handling so lost connections are gracefully re-established without crashing the consumer thread.

3. Dashboard Auto-Refresh & UI Visual Polish
- Live Refresh: Integrated streamlit_autorefresh to poll PostgreSQL every 3 seconds for automated real-time feeds without manual browser reloads.
- Color Mapping: Mapped is_anomaly flags in Plotly scatter charts to distinct hex colors (#4A5568 for normal vs. #FF4B4B for flagged fraud) for instant visual detection.
