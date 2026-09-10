import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Fraud Detection ML Service")

model = None

@app.on_event("startup")
def load_model():
    global model
    try:
        model = joblib.load("/app/model/model.pkl")
    except Exception as e:
        print(f"Failed to load model: {e}")

class Transaction(BaseModel):
    amount: float
    location_code: int
    device_code: int

@app.post("/predict")
def predict(transaction: Transaction):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    data = pd.DataFrame([transaction.dict()])
    # Isolation Forest outputs -1 for anomalies and 1 for normal values.
    prediction = model.predict(data)[0]
    # Lower/more negative score indicates a higher degree of anomaly.
    raw_score = model.score_samples(data)[0]
    
    # Standardize anomaly score representation (0 to 1 scale for clarity)
    anomaly_score = round(float(-raw_score), 4)
    is_anomaly = bool(prediction == -1)

    return {"is_anomaly": is_anomaly, "anomaly_score": anomaly_score}