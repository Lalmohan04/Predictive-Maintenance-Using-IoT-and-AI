import sqlite3
import pickle
import numpy as np
import time
from sklearn.ensemble import IsolationForest
from sklearn.utils.validation import check_is_fitted

# **Thresholds to Reduce False Alerts**
TEMP_THRESHOLD = 35.0
VIBRATION_THRESHOLD = 17.0
HUMIDITY_THRESHOLD = 80.0

# **Model File Path**
MODEL_PATH = "isolation_forest_model.pkl"

# **Ensure sensor_data.db and Table Exists**
def initialize_sensor_db():
    conn = sqlite3.connect("sensor_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            timestamp TEXT PRIMARY KEY,
            temperature REAL,
            humidity REAL,
            vibration REAL
        )
    """)
    conn.commit()
    conn.close()

initialize_sensor_db()  # Ensure table exists before fetching data

# **Function to Train & Save Isolation Forest Model**
def train_isolation_forest():
    print("🚀 Training a new Isolation Forest model...")
    model = IsolationForest(contamination=0.05, random_state=42)

    # Simulated training data (Replace with real sensor data)
    training_data = np.random.rand(100, 1) * 100  
    model.fit(training_data)

    # Save the trained model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print("✅ Isolation Forest Model Trained and Saved Successfully!")
    return model

# **Load or Train Isolation Forest Model**
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    # ✅ Verify if the model is fitted
    check_is_fitted(model)
    print("✅ Loaded and verified Isolation Forest model.")
except (FileNotFoundError, pickle.UnpicklingError, EOFError):
    print("⚠️ Model file not found or corrupted. Training a new one...")
    model = train_isolation_forest()
except Exception as e:
    print(f"❌ Error loading model: {e}")
    exit()

# **Ensure Anomalies Table Exists**
def initialize_anomalies_db():
    conn = sqlite3.connect("anomalies.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temperature REAL,
            humidity REAL,
            vibration REAL
        )
    """)
    conn.commit()
    conn.close()

initialize_anomalies_db()  # Ensure table exists before logging anomalies

# **Function to Fetch Latest Sensor Data from SQLite**
def get_latest_sensor_data():
    conn = sqlite3.connect("sensor_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, temperature, humidity, vibration FROM sensor_readings ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "timestamp": row[0],
            "temperature": row[1],
            "humidity": row[2],
            "vibration": row[3]
        }
    else:
        return None  # No data available

# **Function to Log Anomalies in SQLite**
def log_anomaly(timestamp, temperature=None, humidity=None, vibration=None):
    conn = sqlite3.connect("anomalies.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO anomalies (timestamp, temperature, humidity, vibration) 
        VALUES (?, ?, ?, ?)
    """, (timestamp, temperature, humidity, vibration))
    conn.commit()
    conn.close()
    print(f"📝 Logged anomaly at {timestamp}")

# **Main Anomaly Detection Loop**
while True:
    sensor_data = get_latest_sensor_data()
    if not sensor_data:
        print("⚠️ No sensor data found. Waiting for new data...")
        time.sleep(5)
        continue

    timestamp = sensor_data["timestamp"]
    anomaly_detected = False
    temperature = humidity = vibration = None

    for sensor in ["temperature", "humidity", "vibration"]:
        value = sensor_data[sensor]
        alert = False  # Reset alert for each sensor

        print(f"DEBUG: {sensor} Value = {value}, Threshold = {TEMP_THRESHOLD if sensor == 'temperature' else HUMIDITY_THRESHOLD if sensor == 'humidity' else VIBRATION_THRESHOLD}")

        # **Step 1: Check Manual Thresholds**
        if sensor == "temperature" and value > TEMP_THRESHOLD:
            alert = True
        elif sensor == "humidity" and value > HUMIDITY_THRESHOLD:
            alert = True
        elif sensor == "vibration" and value > VIBRATION_THRESHOLD:
            alert = True

        # **Step 2: Apply Isolation Forest (Only if Manual Threshold Didn't Trigger)**
        if model is not None and not alert:
            prediction = model.predict(np.array([[value]]))
            if prediction[0] == -1:
                alert = True

        # **Step 3: Store Anomalies if Detected**
        if alert:
            print(f"⚠️ ALERT! {sensor}: {value} -> Anomalous")
            anomaly_detected = True

            if sensor == "temperature":
                temperature = value
            elif sensor == "humidity":
                humidity = value
            elif sensor == "vibration":
                vibration = value

    # **Step 4: Log Anomalies in Database**
    if anomaly_detected:
        log_anomaly(timestamp, temperature, humidity, vibration)

    time.sleep(5)  # Delay before next check
