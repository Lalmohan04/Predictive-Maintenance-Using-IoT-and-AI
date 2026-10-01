import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import tensorflow as tf
from tensorflow.keras.models import load_model
import plotly.express as px
import time
import paho.mqtt.client as mqtt
import json

# **Database Setup**
conn = sqlite3.connect("sensor_data.db", check_same_thread=False)
c = conn.cursor()

# **Load LSTM Model**
try:
    model = load_model("lstm_anomaly_model.h5", compile=False)
    model.compile(optimizer="adam", loss="mae")
except Exception as e:
    st.error(f"❌ Failed to load LSTM Model: {str(e)}")
    model = None

# **Streamlit UI**
st.title("🔧 Predictive Maintenance Dashboard")

# **Employee Login**
employee_id = st.text_input("Enter Employee ID to access dashboard:")
if not employee_id:
    st.warning("Please enter your Employee ID.")
    st.stop()

# **MQTT Setup**
BROKER = "4fa8f8b74ffc487783cc25a7dc43d1e6.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "Myiot"
PASSWORD = "Myiot123"
TOPICS = ["sensor/temperature", "sensor/humidity", "sensor/vibration"]

data_store = {"temperature": None, "humidity": None, "vibration": None}

# **MQTT Callbacks**
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT Connected Successfully")
        for topic in TOPICS:
            client.subscribe(topic)
    else:
        print(f"❌ MQTT Connection Failed, Return Code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if "temperature" in payload:
            data_store["temperature"] = float(payload["temperature"])
        if "humidity" in payload:
            data_store["humidity"] = float(payload["humidity"])
        if "vibration" in payload:
            data_store["vibration"] = float(payload["vibration"])
            
        c.execute("INSERT INTO sensor_data (timestamp, temperature, humidity, vibration) VALUES (?, ?, ?, ?)", 
                  (timestamp, data_store["temperature"], data_store["humidity"], data_store["vibration"]))
        conn.commit()
    except Exception as e:
        print(f"❌ Error processing MQTT message from {msg.topic}: {str(e)}")

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

# **Historical Data Storage**
if "historical_data" not in st.session_state:
    st.session_state.historical_data = pd.DataFrame(columns=["timestamp", "temperature", "humidity", "vibration"])

# **Fetch Data Function**
@st.cache_data(ttl=5)
def fetch_data():
    df = pd.read_sql_query("""
        SELECT timestamp, temperature, humidity, vibration
        FROM sensor_data
        ORDER BY timestamp DESC
        LIMIT 100
    """, conn)
    df["timestamp"] = pd.to_datetime(df["timestamp"])  # Ensure timestamp is datetime
    return df

# **Update Historical Data**
new_data = fetch_data()
if not new_data.empty:
    new_data["timestamp"] = pd.to_datetime(new_data["timestamp"])  # Convert to datetime
    st.session_state.historical_data = pd.concat([st.session_state.historical_data, new_data])
    st.session_state.historical_data = st.session_state.historical_data.drop_duplicates().sort_values("timestamp")

df = st.session_state.historical_data

if not df.empty:
    latest_temp = df["temperature"].iloc[-1]
    latest_hum = df["humidity"].iloc[-1]
    latest_vib = df["vibration"].iloc[-1]
else:
    st.warning("No sensor data available. Waiting for data...")
    latest_temp, latest_hum, latest_vib = None, None, None

# **Real-Time Gauge Indicators**
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="🌡️ Temperature", value=f"{latest_temp:.2f} °C" if latest_temp is not None else "Waiting...")
with col2:
    st.metric(label="💧 Humidity", value=f"{latest_hum:.2f} %" if latest_hum is not None else "Waiting...")
with col3:
    st.metric(label="🔄 Vibration", value=f"{latest_vib:.2f} g" if latest_vib is not None else "Waiting...")

# **Alerts**
if latest_temp is not None:
    if latest_temp > 35:
        st.error("🔥 High Temperature Alert! Immediate action required.")
    elif latest_temp < 10:
        st.warning("❄️ Temperature too low! Check system conditions.")
if latest_hum is not None:
    if latest_hum > 80:
        st.error("💦 High Humidity Alert! Potential moisture damage risk.")
    elif latest_hum < 20:
        st.warning("🌵 Low Humidity Alert! Possible dryness-related issues.")
if latest_vib is not None and latest_vib > 17:
    st.error("🔴 Excessive Vibration Detected! Machine might be unstable.")

# **Maintenance Scheduling**
next_maintenance = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 86400))
st.write(f"🛠️ **Next scheduled maintenance:** {next_maintenance}")

# **Historical & Real-Time Data Visualization**
st.write("### 📊 Sensor Data Trends (Real-Time Historical Data)")
fig = px.line(df, x="timestamp", y=["temperature", "humidity", "vibration"],
              labels={"value": "Sensor Readings", "timestamp": "Time"},
              title="Sensor Readings Over Time")
st.plotly_chart(fig, use_container_width=True)

## **Anomaly Detection & Maintenance Scheduling**
seq_length = 10
if len(df) >= seq_length and model is not None:
    try:
        data_values = df[["temperature", "humidity", "vibration"]].dropna().values[-seq_length:]
        if data_values.shape == (seq_length, 3):
            data_values = np.expand_dims(data_values, axis=0)  # Reshape for LSTM input
            prediction = model.predict(data_values)  # Model prediction
            predicted_value = prediction[0, 0]
            actual_value = data_values[0, 0, 0]
            anomaly_threshold = 0.1
            if abs(predicted_value - actual_value) > anomaly_threshold:
                st.error(f"🚨 Anomaly Detected! Immediate maintenance required.")
                next_maintenance = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 43200))
            else:
                st.success("✅ System running normally.")
    except Exception as e:
        st.error(f"❌ Error in Anomaly Detection: {str(e)}")

st.write(f"🛠️ **Next scheduled maintenance:** {next_maintenance}")
time.sleep(10)
st.rerun()
