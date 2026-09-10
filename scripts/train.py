import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

def generate_synthetic_data(n_samples=5000):
    np.random.seed(42)
    # Normal transactions: lower amounts, routine locations/devices
    normal_amounts = np.random.exponential(scale=50, size=int(n_samples * 0.95))
    normal_locations = np.random.choice([0, 1, 2], size=int(n_samples * 0.95)) # 0: US, 1: CA, 2: UK
    normal_devices = np.random.choice([0, 1], size=int(n_samples * 0.95))     # 0: Mobile, 1: Web

    # Fraudulent transactions: high amounts, unusual locations/devices
    fraud_amounts = np.random.uniform(low=800, high=5000, size=int(n_samples * 0.05))
    fraud_locations = np.random.choice([3, 4], size=int(n_samples * 0.05))    # 3: High-risk A, 4: High-risk B
    fraud_devices = np.random.choice([2], size=int(n_samples * 0.05))         # 2: Unknown API

    amounts = np.concatenate([normal_amounts, fraud_amounts])
    locations = np.concatenate([normal_locations, fraud_locations])
    devices = np.concatenate([normal_devices, fraud_devices])

    df = pd.DataFrame({'amount': amounts, 'location_code': locations, 'device_code': devices})
    return df

if __name__ == "__main__":
    df = generate_synthetic_data()
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(df)

    os.makedirs("model", exist_ok=True)
    joblib.dump(model, "model/model.pkl")
    print("Model successfully trained and saved to model/model.pkl")
