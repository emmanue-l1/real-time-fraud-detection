import os
import json
import time
import requests
import psycopg2
from kafka import KafkaConsumer
from openai import OpenAI

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "fraud_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "adminpassword")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml_service:8000/predict")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def wait_for_ml_service():
    """Wait until the FastAPI service is healthy and ready to serve predictions."""
    print("Waiting for ML Service to be ready...")
    # Hit root or a simple GET to check availability
    health_url = ML_SERVICE_URL.rsplit('/', 1)[0] + "/docs"
    while True:
        try:
            resp = requests.get(health_url, timeout=2)
            if resp.status_code == 200:
                print("ML Service is up and ready!")
                break
        except Exception:
            pass
        time.sleep(2)

def get_db_connection():
    """Connect to Postgres with retry logic."""
    print("Connecting to PostgreSQL...")
    while True:
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST, database=POSTGRES_DB,
                user=POSTGRES_USER, password=POSTGRES_PASSWORD
            )
            print("Connected to PostgreSQL!")
            return conn
        except Exception as e:
            time.sleep(2)

def generate_llm_explanation(event, score):
    if not openai_client:
        return "LLM integration disabled (Missing API Key)."
    
    prompt = f"""
    Anomalous financial transaction detected:
    - User ID: {event['user_id']}
    - Amount: ${event['amount']}
    - Location: {event['location']}
    - Device: {event['device_type']}
    - Anomaly Score: {score}

    Provide a concise 2-sentence plain English explanation of why this transaction is suspicious for risk analysts.
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating explanation: {str(e)}"

if __name__ == "__main__":
    # Block until downstream microservices are fully live
    wait_for_ml_service()
    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    # Wait for Kafka Broker
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                "transactions",
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest'
            )
        except Exception as e:
            print(f"Waiting for Kafka broker... ({e})")
            time.sleep(3)

    print("Consumer active. Processing streams...")

    for message in consumer:
        event = message.value
        payload = {
            "amount": event["amount"],
            "location_code": event["location_code"],
            "device_code": event["device_code"]
        }
        
        try:
            ml_resp = requests.post(ML_SERVICE_URL, json=payload, timeout=5).json()
            is_anomaly = ml_resp["is_anomaly"]
            anomaly_score = ml_resp["anomaly_score"]
        except Exception as e:
            print(f"ML Service Request Failed: {e}")
            continue

        llm_explanation = None
        if is_anomaly:
            llm_explanation = generate_llm_explanation(event, anomaly_score)

        query = """
        INSERT INTO fraud_events (transaction_id, user_id, amount, location, device_type, timestamp, anomaly_score, is_anomaly, llm_explanation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (transaction_id) DO NOTHING;
        """
        
        # Guard DB connections against timeouts
        try:
            cursor.execute(query, (
                event["transaction_id"], event["user_id"], event["amount"],
                event["location"], event["device_type"], event["timestamp"],
                anomaly_score, is_anomaly, llm_explanation
            ))
            db_conn.commit()
        except psycopg2.OperationalError:
            print("Database connection lost. Reconnecting...")
            db_conn = get_db_connection()
            cursor = db_conn.cursor()