import os
import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

st.set_page_config(page_title="Real-Time Fraud Monitoring", layout="wide")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "fraud_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "adminpassword")

def load_data():
    conn = psycopg2.connect(
        host=POSTGRES_HOST, database=POSTGRES_DB,
        user=POSTGRES_USER, password=POSTGRES_PASSWORD
    )
    query = "SELECT * FROM fraud_events ORDER BY timestamp DESC LIMIT 200;"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.title("🛡️ Real-Time Anomaly & Fraud Detection Center")

df = load_data()

if not df.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Transactions Analyzed", len(df))
    m2.metric("Anomalies Flagged", len(df[df['is_anomaly'] == True]))
    m3.metric("Highest Anomaly Score", f"{df['anomaly_score'].max():.4f}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Transaction Amount vs Anomaly Score")
        fig = px.scatter(df, x="amount", y="anomaly_score", color="is_anomaly",
                         hover_data=["user_id", "location", "device_type"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Anomalies by Location")
        anomaly_df = df[df['is_anomaly'] == True]
        if not anomaly_df.empty:
            fig2 = px.histogram(anomaly_df, x="location", color="device_type")
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Recent Flagged Anomalies & AI Explanations")
    anomalies_only = df[df['is_anomaly'] == True][['timestamp', 'user_id', 'amount', 'location', 'device_type', 'anomaly_score', 'llm_explanation']]
    st.dataframe(anomalies_only, use_container_width=True)
else:
    st.warning("No transaction data available yet.")

if st.button("Refresh Feed"):
    st.rerun()