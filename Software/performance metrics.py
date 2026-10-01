from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error
import time
import numpy as np
import tensorflow as tf
import sqlite3
import pandas as pd

# Load trained LSTM model
try:
    model = tf.keras.models.load_model("lstm_anomaly_model.h5", compile=False)
except Exception as e:
    print(f"❌ Error loading model: {str(e)}")
    exit()

# Load dataset for evaluation
def load_data():
    conn = sqlite3.connect("sensor_data.db")
    df = pd.read_sql_query("SELECT temperature, humidity, vibration FROM sensor_readings ORDER BY timestamp DESC LIMIT 100", conn)
    conn.close()
    return df.dropna()

data = load_data()

# Ensure correct input shape for LSTM
if len(data) < 10:
    print("⚠️ Not enough data for LSTM sequence prediction (min 10 samples required). Exiting...")
    exit()

# Create sequences for LSTM
def create_sequences(data, seq_length=10):
    X = []
    for i in range(len(data) - seq_length):
        X.append(data.iloc[i:i + seq_length].values)
    return np.array(X)

X_test = create_sequences(data)

if len(X_test) == 0:
    print("⚠️ Not enough data to create sequences for LSTM. Exiting...")
    exit()

# Simulated Ground Truth (for evaluation purpose)
true_labels = np.random.choice([0, 1], size=len(X_test), p=[0.90, 0.10])  # 90% normal, 10% anomalies

# Predict anomalies using trained LSTM model
def detect_anomalies_lstm(X_test):
    predictions = model.predict(X_test).flatten()
    threshold = np.percentile(predictions, 85)  # 🔥 Lowered threshold from 95% to 90%
    predicted_labels = (predictions > threshold).astype(int)

    # Ensure we have at least one anomaly predicted
    if np.sum(predicted_labels) == 0:
        predicted_labels[np.argmax(predictions)] = 1  # Force at least one anomaly
    return predicted_labels

predicted_labels = detect_anomalies_lstm(X_test)

# Ensure label consistency
if len(true_labels) != len(predicted_labels):
    print(f"❌ Mismatch in label lengths: true_labels={len(true_labels)}, predicted_labels={len(predicted_labels)}")
    exit()

# Compute evaluation metrics (Handling Zero Division)
accuracy = accuracy_score(true_labels, predicted_labels)
precision = precision_score(true_labels, predicted_labels, zero_division=1)
recall = recall_score(true_labels, predicted_labels, zero_division=1)
f1 = f1_score(true_labels, predicted_labels, zero_division=1)
mse = mean_squared_error(true_labels, predicted_labels)

# Measure latency for real-time MQTT & Streamlit dashboard
def measure_latency():
    start_time = time.time()
    load_data()
    detect_anomalies_lstm(X_test)
    end_time = time.time()
    return end_time - start_time

latency = measure_latency()

# Print Results
print(f"✅ Accuracy: {accuracy:.4f}")
print(f"🎯 Precision: {precision:.4f}")
print(f"📈 Recall: {recall:.4f}")
print(f"⚖️ F1-Score: {f1:.4f}")
print(f"📉 Mean Squared Error (MSE): {mse:.4f}")
print(f"⏳ Latency: {latency:.4f} seconds")
