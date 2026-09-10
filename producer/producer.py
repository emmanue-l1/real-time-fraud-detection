import os
import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from faker import Faker
import numpy as np

fake = Faker()
bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Retries wait for Kafka broker startup
producer = None
for _ in range(10):
    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        break
    except Exception:
        time.sleep(3)

LOCATION_MAP = {"US": 0, "CA": 1, "UK": 2, "High-Risk-A": 3, "High-Risk-B": 4}
DEVICE_MAP = {"Mobile": 0, "Web": 1, "API-Unknown": 2}

def generate_transaction():
    is_fraud = random.random() < 0.08  # ~8% anomaly rate
    
    if is_fraud:
        amount = round(random.uniform(800.0, 5000.0), 2)
        location = random.choice(["High-Risk-A", "High-Risk-B"])
        device = "API-Unknown"
    else:
        amount = round(np.random.exponential(scale=40.0), 2) + 1.0
        location = random.choice(["US", "CA", "UK"])
        device = random.choice(["Mobile", "Web"])

    return {
        "transaction_id": fake.uuid4(),
        "user_id": f"usr_{random.randint(1000, 1050)}",
        "amount": amount,
        "location": location,
        "location_code": LOCATION_MAP[location],
        "device_type": device,
        "device_code": DEVICE_MAP[device],
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    print("Starting Kafka Producer...")
    while True:
        event = generate_transaction()
        producer.send("transactions", value=event)
        time.sleep(random.uniform(0.5, 1.5))