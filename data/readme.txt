#include <Wire.h>
#include <DHT.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <math.h>  // For sqrt()

// WiFi Credentials
const char* ssid = "WIFI";
const char* password = "123456789";

// MQTT Broker Credentials
const char* mqtt_server = "4fa8f8b74ffc487783cc25a7dc43d1e6.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "Myiot";
const char* mqtt_password = "Myiot123";

// MQTT Topics
const char* topic_temp = "sensor/temperature";
const char* topic_humidity = "sensor/humidity";
const char* topic_vibration = "sensor/vibration";  // New Topic for Vibration

// DHT11 Configuration
#define DHTPIN D4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// MPU6050 Configuration
const int MPU_ADDR = 0x68;  // I2C address of MPU6050
int16_t AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ;

// WiFi & MQTT Clients
WiFiClientSecure espClient;
PubSubClient client(espClient);

// Function to Connect WiFi
void setup_wifi() {
    delay(10);
    Serial.println("Connecting to WiFi...");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi Connected.");
}

// Function to Reconnect MQTT
void reconnect_mqtt() {
    while (!client.connected()) {
        Serial.print("Connecting to MQTT...");
        if (client.connect("ESP8266Client", mqtt_user, mqtt_password)) {
            Serial.println("Connected.");
        } else {
            Serial.print("Failed, rc=");
            Serial.print(client.state());
            Serial.println(" Trying again in 5 seconds...");
            delay(5000);
        }
    }
}

// Function to Initialize MPU6050 Manually
void initMPU6050() {
    Wire.beginTransmission(MPU_ADDR);
    if (Wire.endTransmission() == 0) {
        Serial.println("MPU6050 is connected!");
    } else {
        Serial.println("MPU6050 NOT found! Check connections.");
        while (1);
    }

    // Wake up MPU6050
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x6B);
    Wire.write(0);  
    Wire.endTransmission(true);
}

// Setup Function
void setup() {
    Serial.begin(115200);
    Wire.begin();
    dht.begin();
    setup_wifi();
    espClient.setInsecure();  
    client.setServer(mqtt_server, mqtt_port);
    initMPU6050();  // Initialize MPU6050 Manually
}

// Function to Read and Publish Sensor Data
void publish_sensor_data() {
    // Read Temperature & Humidity
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    // Read MPU6050 Data
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x3B);  
    Wire.endTransmission(false);
    Wire.requestFrom(MPU_ADDR, 14, true);

    AcX = Wire.read() << 8 | Wire.read();
    AcY = Wire.read() << 8 | Wire.read();
    AcZ = Wire.read() << 8 | Wire.read();
    Tmp = Wire.read() << 8 | Wire.read();
    GyX = Wire.read() << 8 | Wire.read();
    GyY = Wire.read() << 8 | Wire.read();
    GyZ = Wire.read() << 8 | Wire.read();

    // Compute Vibration (Magnitude)
    float vibration = sqrt(AcX * AcX + AcY * AcY + AcZ * AcZ + GyX * GyX + GyY * GyY + GyZ * GyZ) / 1000.0;


    // Convert Sensor Data to JSON Format
    String json_temp = "{\"temperature\": " + String(temperature) + "}";
    String json_humidity = "{\"humidity\": " + String(humidity) + "}";
    String json_vibration = "{\"vibration\": " + String(vibration) + "}";  // New JSON

    // Publish Data to MQTT Topics
    client.publish(topic_temp, json_temp.c_str());
    client.publish(topic_humidity, json_humidity.c_str());
    client.publish(topic_vibration, json_vibration.c_str());  // Publish Vibration

    Serial.println("✅ Published Sensor Data.");
}

// Main Loop
void loop() {
    if (!client.connected()) {
        reconnect_mqtt();
    }
    client.loop();
    publish_sensor_data();
    delay(5000);  // Publish every 5 seconds
}

output  IDE 
..
WiFi Connected.
MPU6050 is connected!
Connecting to MQTT...Connected.
✅ Published Sensor Data.
✅ Published Sensor Data

output in WebClient hivemq 
Topic: sensor/temperature
QoS: 0
{"temperature": 29.80}
Topic: sensor/humidity
QoS: 0
{"humidity": 78.30}
Topic: sensor/vibration
QoS: 0
{"vibration": 16.50}


## now Sqlite + mqtt hivemq


import paho.mqtt.client as mqtt
import sqlite3
import json
from datetime import datetime

# MQTT Broker details
BROKER = "4fa8f8b74ffc487783cc25a7dc43d1e6.s1.eu.hivemq.cloud"
PORT = 8883
TOPICS = ["sensor/temperature", "sensor/humidity", "sensor/vibration"]

# Dictionary to hold sensor data
sensor_data = {"temperature": None, "humidity": None, "vibration": None}

# SQLite Connection
conn = sqlite3.connect("sensor_data.db", check_same_thread=False)
cursor = conn.cursor()

# Create Table (if not exists)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_readings (
        timestamp TEXT PRIMARY KEY,
        temperature REAL,
        humidity REAL,
        vibration REAL
    )
""")
conn.commit()

# Function to insert data into SQLite
def insert_data(temperature, humidity, vibration):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO sensor_readings (timestamp, temperature, humidity, vibration)
        VALUES (?, ?, ?, ?)
    """, (timestamp, temperature, humidity, vibration))
    conn.commit()
    print(f"💾 Data inserted: {timestamp}, {temperature}, {humidity}, {vibration}")

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        for topic in TOPICS:
            client.subscribe(topic)
            print(f"📡 Subscribed to {topic}")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")  # Decode the payload
        data = json.loads(payload)  # Parse JSON

        if msg.topic == "sensor/temperature":
            sensor_data["temperature"] = float(data["temperature"])
        elif msg.topic == "sensor/humidity":
            sensor_data["humidity"] = float(data["humidity"])
        elif msg.topic == "sensor/vibration":
            sensor_data["vibration"] = float(data["vibration"])

        print(f"📩 Received `{data}` from `{msg.topic}` topic")
        
        # Store data in SQLite (only if all values are received)
        if all(v is not None for v in sensor_data.values()):
            insert_data(sensor_data["temperature"], sensor_data["humidity"], sensor_data["vibration"])
            sensor_data.update({"temperature": None, "humidity": None, "vibration": None})

    except json.JSONDecodeError:
        print(f"⚠️ Error: Received malformed JSON: {payload}")
    except KeyError:
        print(f"⚠️ Error: Missing expected key in payload: {payload}")
    except ValueError:
        print(f"⚠️ Error: Could not convert data to float: {payload}")

# MQTT Setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.tls_set()  # Enable SSL
client.username_pw_set("Myiot", "Myiot123")

# Connect & Start Loop
client.connect(BROKER, PORT, 60)
client.loop_forever()

output shown in vs code terminal
PS C:\Users\saipa\.vscode\sem6> & C:/Users/saipa/AppData/Local/Programs/Python/Python310/python.exe c:/Users/saipa/.vscode/sem6/mqtt2sqlite.py
c:\Users\saipa\.vscode\sem6\mqtt2sqlite.py:76: DeprecationWarning: Callback API version 1 is deprecated, update to latest version
  client = mqtt.Client()
✅ Connected to MQTT Broker!
📡 Subscribed to sensor/temperature
📡 Subscribed to sensor/humidity
📡 Subscribed to sensor/vibration
📩 Received `{'temperature': 29.9}` from `sensor/temperature` topic
📩 Received `{'humidity': 77.1}` from `sensor/humidity` topic
📩 Received `{'vibration': 16.49}` from `sensor/vibration` topic
💾 Data inserted: 2025-03-15 23:00:27, 29.9, 77.1, 16.49
 output in files one file has created as "sensor_data.db"

###Anomaly_detection 
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

output in the vs code terminal
PS C:\Users\saipa\.vscode\sem6> & C:/Users/saipa/AppData/Local/Programs/Python/Python310/python.exe c:/Users/saipa/.vscode/sem6/IFM.py      
✅ Loaded and verified Isolation Forest model.
DEBUG: temperature Value = 29.9, Threshold = 35.0
DEBUG: humidity Value = 76.5, Threshold = 80.0
DEBUG: vibration Value = 16.48, Threshold = 17.0
DEBUG: temperature Value = 29.9, Threshold = 35.0
DEBUG: humidity Value = 76.5, Threshold = 80.0
DEBUG: vibration Value = 16.48, Threshold = 17.0
DEBUG: temperature Value = 29.9, Threshold = 35.0
DEBUG: humidity Value = 76.5, Threshold = 80.0
DEBUG: vibration Value = 16.53, Threshold = 17.0
DEBUG: temperature Value = 29.9, Threshold = 35.0
DEBUG: humidity Value = 76.5, Threshold = 80.0
DEBUG: vibration Value = 21.26, Threshold = 17.0
⚠️ ALERT! vibration: 21.26 -> Anomalous
📝 Logged anomaly at 2025-03-15 23:04:41

file created isolation_forest_model.pkl and anomalies.db

####clean the data for lstm model


import sqlite3
import pandas as pd
import numpy as np

# ✅ Connect to SQLite database
db_path = r"C:\Users\saipa\.vscode\sem6\sensor_data.db"
conn = sqlite3.connect(db_path)

# ✅ Corrected table name (`sensor_readings`)
query = "SELECT timestamp, temperature, humidity, vibration FROM sensor_readings"
df = pd.read_sql_query(query, conn)
conn.close()

# ✅ Ensure all expected columns exist
expected_sensors = ["temperature", "humidity", "vibration"]
for sensor in expected_sensors:
    if sensor not in df.columns:
        df[sensor] = np.nan  # Fill missing columns with NaN

# ✅ Handle missing data
df.ffill(inplace=True)  # Forward fill missing values
df.bfill(inplace=True)  # Backward fill missing values

# ✅ Save the cleaned data
df.to_csv("lstm_ready_data.csv", index=False)
print("✅ Cleaned data saved as lstm_ready_data.csv for LSTM training!")
output in terminal

PS C:\Users\saipa\.vscode\sem6> & C:/Users/saipa/AppData/Local/Programs/Python/Python310/python.exe c:/Users/saipa/.vscode/sem6/cleandata.py
✅ Cleaned data saved as lstm_ready_data.csv for LSTM training!
file saved as lstm_ready_data.csv 


#### now lstm aldo code

import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import joblib
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

# 1️⃣ Load dataset
print("🔄 Loading dataset...")
df = pd.read_csv("lstm_ready_data.csv", parse_dates=["timestamp"])

if df.empty:
    raise ValueError("❌ Error: Loaded dataset is empty! Check lstm_ready_data.csv")

df.ffill(inplace=True)  # Forward fill missing values
df.drop(columns=["timestamp"], inplace=True)  # Drop timestamp for LSTM processing

# 2️⃣ Scale data (0 to 1) and save scaler
scaler = MinMaxScaler()
df_scaled = scaler.fit_transform(df)
joblib.dump(scaler, "scaler.pkl")  # Save scaler for inference

# 3️⃣ Create sequences for LSTM
def create_sequences(data, seq_length=10):
    if len(data) <= seq_length:
        raise ValueError(f"❌ Error: Not enough data for sequence length {seq_length}")
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length, 0])  # Predicting temperature
    return np.array(X), np.array(y)

seq_length = 10
X, y = create_sequences(df_scaled, seq_length)

# 4️⃣ Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# 5️⃣ Build LSTM Model
print("🛠️ Building LSTM model...")
model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(seq_length, X.shape[2])),
    Dropout(0.2),
    LSTM(32, return_sequences=False),
    Dropout(0.2),
    Dense(1)
])

model.compile(optimizer="adam", loss="mae")
model.summary()

# 6️⃣ Train Model with Early Stopping
print("🚀 Training model...")
early_stopping = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)
history = model.fit(X_train, y_train, epochs=50, batch_size=16, validation_data=(X_test, y_test), callbacks=[early_stopping])

# Save model
model.save("lstm_anomaly_model.h5")
print("✅ Model saved as lstm_anomaly_model.h5")

# 7️⃣ Detect Anomalies
print("🔍 Detecting anomalies...")
predictions = model.predict(X_test).flatten()

# Compute anomaly scores
deviation = np.abs(predictions - y_test)

# Set dynamic anomaly threshold (95th percentile)
thresh = np.percentile(deviation, 95)

# Detect anomalies
anomalies = np.where(deviation > thresh)[0]
print(f"⚠️ Anomalies detected at indices: {anomalies}")

# Save anomaly data for debugging
np.save("predictions.npy", predictions)
np.save("actual.npy", y_test)
np.save("anomalies.npy", anomalies)

# 8️⃣ Save training loss plot
plt.figure(figsize=(8,5))
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.legend()
plt.title("LSTM Training Loss")
plt.savefig("training_loss_plot.png")
print("📊 Training loss plot saved as training_loss_plot.png")

# 🔍 9️⃣ Visualize Detected Anomalies
plt.figure(figsize=(10,5))
plt.plot(range(len(y_test)), y_test, label="Actual Temperature", color="blue")
plt.plot(range(len(predictions)), predictions, label="Predicted Temperature", color="orange")
plt.scatter(anomalies, y_test[anomalies], color="red", label="Anomalies", marker="x")
plt.xlabel("Time Index")
plt.ylabel("Temperature (Scaled)")
plt.title("Temperature Anomaly Detection")
plt.legend()
plt.show()
 
 output in terminal vs code 
 PS C:\Users\saipa\.vscode\sem6> & C:/Users/saipa/AppData/Local/Programs/Python/Python310/python.exe c:/Users/saipa/.vscode/sem6/lstm_anomaly_detection.py
2025-03-15 23:32:10.798888: I tensorflow/core/util/port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
2025-03-15 23:32:12.227662: I tensorflow/core/util/port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
🔄 Loading dataset...
🛠️ Building LSTM model...
2025-03-15 23:32:15.994216: I tensorflow/core/platform/cpu_feature_guard.cc:210] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 AVX512F AVX512_VNNI FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
C:\Users\saipa\AppData\Local\Programs\Python\Python310\lib\site-packages\keras\src\layers\rnn\rnn.py:200: UserWarning: Do not pass an `input_shape`/`input_dim` argument to a layer. When using Sequential models, prefer using an `Input(shape)` object as the first layer in the model instead.
  super().__init__(**kwargs)
Model: "sequential"
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Layer (type)                         ┃ Output Shape                ┃         Param # ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ lstm (LSTM)                          │ (None, 10, 64)              │          17,408 │
├──────────────────────────────────────┼─────────────────────────────┼─────────────────┤
│ dropout (Dropout)                    │ (None, 10, 64)              │               0 │
├──────────────────────────────────────┼─────────────────────────────┼─────────────────┤
│ lstm_1 (LSTM)                        │ (None, 32)                  │          12,416 │
├──────────────────────────────────────┼─────────────────────────────┼─────────────────┤
│ dropout_1 (Dropout)                  │ (None, 32)                  │               0 │
├──────────────────────────────────────┼─────────────────────────────┼─────────────────┤
│ dense (Dense)                        │ (None, 1)                   │              33 │
└──────────────────────────────────────┴─────────────────────────────┴─────────────────┘
 Total params: 29,857 (116.63 KB)
 Trainable params: 29,857 (116.63 KB)
 Non-trainable params: 0 (0.00 B)
🚀 Training model...
Epoch 1/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 5s 13ms/step - loss: 0.0425 - val_loss: 0.0193
Epoch 2/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 10ms/step - loss: 0.0213 - val_loss: 0.0217
Epoch 3/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 10ms/step - loss: 0.0173 - val_loss: 0.0174
Epoch 4/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 2s 12ms/step - loss: 0.0134 - val_loss: 0.0215
Epoch 5/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 10ms/step - loss: 0.0133 - val_loss: 0.0174
Epoch 6/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 9ms/step - loss: 0.0111 - val_loss: 0.0162
Epoch 7/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 9ms/step - loss: 0.0115 - val_loss: 0.0165
Epoch 8/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 2s 11ms/step - loss: 0.0105 - val_loss: 0.0126
Epoch 9/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 2s 12ms/step - loss: 0.0105 - val_loss: 0.0134
Epoch 10/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 2s 9ms/step - loss: 0.0106 - val_loss: 0.0121
Epoch 11/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 9ms/step - loss: 0.0107 - val_loss: 0.0120
Epoch 12/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 10ms/step - loss: 0.0092 - val_loss: 0.0086
Epoch 13/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 10ms/step - loss: 0.0082 - val_loss: 0.0073
Epoch 14/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 2s 11ms/step - loss: 0.0088 - val_loss: 0.0082
Epoch 15/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 9ms/step - loss: 0.0089 - val_loss: 0.0103
Epoch 16/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 9ms/step - loss: 0.0093 - val_loss: 0.0081
Epoch 17/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 9ms/step - loss: 0.0083 - val_loss: 0.0072
Epoch 18/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 2s 11ms/step - loss: 0.0074 - val_loss: 0.0108
Epoch 19/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 9ms/step - loss: 0.0083 - val_loss: 0.0063
Epoch 20/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 9ms/step - loss: 0.0083 - val_loss: 0.0100
Epoch 21/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 10ms/step - loss: 0.0073 - val_loss: 0.0064
Epoch 22/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 2s 11ms/step - loss: 0.0081 - val_loss: 0.0068
Epoch 23/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 10ms/step - loss: 0.0062 - val_loss: 0.0068
Epoch 24/50
140/140 ━━━━━━━━━━━━━━━━━━━━ 1s 9ms/step - loss: 0.0085 - val_loss: 0.0067
WARNING:absl:You are saving your model as an HDF5 file via `model.save()` or `keras.saving.save_model(model)`. This file format is considered legacy. We recommend using instead the native Keras format, e.g. `model.save('my_model.keras')` or `keras.saving.save_model(model, 'my_model.keras')`.
✅ Model saved as lstm_anomaly_model.h5
🔍 Detecting anomalies...
18/18 ━━━━━━━━━━━━━━━━━━━━ 1s 22ms/step 
⚠️ Anomalies detected at indices: [  3   4   5   6   7   8   9  10  12  16  21  51  81  83  93  94  95  96
  97  98  99 163 164 165 166 167 169 170]
📊 Training loss plot saved as training_loss_plot.png
2 Graphs one lstm traning loss anpther temperature Anomaly detection 
file saved lstm_anomaly_model.h5 and scaler.pkl 


### Dashboard and alret 
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

output in cmd terminal 

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.231:8501

2025-03-15 23:38:44.286934: I tensorflow/core/util/port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
2025-03-15 23:38:47.182187: I tensorflow/core/util/port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
2025-03-15 23:38:56.512832: I tensorflow/core/platform/cpu_feature_guard.cc:210] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 AVX512F AVX512_VNNI FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING:tensorflow:From C:\Users\saipa\AppData\Local\Programs\Python\Python310\lib\site-packages\keras\src\backend\common\global_state.py:82: The name tf.reset_default_graph is deprecated. Please use tf.compat.v1.reset_default_graph instead.

C:\Users\saipa\.vscode\sem6\Predictive Maintenance Dashboard.py:69: DeprecationWarning: Callback API version 1 is deprecated, update to latest version
  client = mqtt.Client()
✅ MQTT Connected Successfully
C:\Users\saipa\.vscode\sem6\Predictive Maintenance Dashboard.py:97: FutureWarning: The behavior of DataFrame concatenation with empty or all-NA entries is deprecated. In a future version, this will no longer exclude empty or all-NA columns when determining the result dtypes. To retain the old behavior, exclude the relevant entries before the concat operation.
  st.session_state.historical_data = pd.concat([st.session_state.historical_data, new_data])
C:\Users\saipa\.vscode\sem6\Predictive Maintenance Dashboard.py:69: DeprecationWarning:

Callback API version 1 is deprecated, update to latest version

✅ MQTT Connected Successfully
C:\Users\saipa\.vscode\sem6\Predictive Maintenance Dashboard.py:69: DeprecationWarning:

Callback API version 1 is deprecated, update to latest version

✅ MQTT Connected Successfully
1/1 ━━━━━━━━━━━━━━━━━━━━ 1s 573ms/step
C:\Users\saipa\.vscode\sem6\Predictive Maintenance Dashboard.py:69: DeprecationWarning:

Callback API version 1 is deprecated, update to latest version

✅ MQTT Connected Successfully
1/1 ━━━━━━━━━━━━━━━━━━━━ 1s 598ms/step
C:\Users\saipa\.vscode\sem6\Predictive Maintenance Dashboard.py:69: DeprecationWarning:

Callback API version 1 is deprecated, update to latest version

✅ MQTT Connected Successfully
1/1 ━━━━━━━━━━━━━━━━━━━━ 1s 636ms/step
C:\Users\saipa\.vscode\sem6\Predictive Maintenance Dashboard.py:69: DeprecationWarning:

Callback API version 1 is deprecated, update to latest version

✅ MQTT Connected Successfully
1/1 ━━━━━━━━━━━━━━━━━━━━ 0s 471ms/step
C:\Users\saipa\.vscode\sem6\Predictive Maintenance Dashboard.py:69: DeprecationWarning:

Callback API version 1 is deprecated, update to latest version

✅ MQTT Connected Successfully
WARNING:tensorflow:5 out of the last 5 calls to <function TensorFlowTrainer.make_predict_function.<locals>.one_step_on_data_distributed at 0x0000025F32E2E5F0> triggered tf.function retracing. Tracing is expensive and the excessive number of tracings could be due to (1) creating @tf.function repeatedly in a loop, (2) passing tensors with different shapes, (3) passing Python objects instead of tensors. For (1), please define your @tf.function outside of the loop. For (2), @tf.function has reduce_retracing=True option that can avoid unnecessary retracing. For (3), please refer to https://www.tensorflow.org/guide/function#controlling_retracing and https://www.tensorflow.org/api_docs/python/tf/function for  more details.
1/1 ━━━━━━━━━━━━━━━━━━━━ 1s 538ms/step
C:\Users\saipa\.vscode\sem6\Predictive Maintenance Dashboard.py:69: DeprecationWarning:

Callback API version 1 is deprecated, update to latest version

✅ MQTT Connected Successfully
WARNING:tensorflow:6 out of the last 6 calls to <function TensorFlowTrainer.make_predict_function.<locals>.one_step_on_data_distributed at 0x0000025F33EE6440> triggered tf.function retracing. Tracing is expensive and the excessive number of tracings could be due to (1) creating @tf.function repeatedly in a loop, (2) passing tensors with different shapes, (3) passing Python objects instead of tensors. For (1), please define your @tf.function outside of the loop. For (2), @tf.function has reduce_retracing=True option that can avoid unnecessary retracing. For (3), please refer to https://www.tensorflow.org/guide/function#controlling_retracing and https://www.tensorflow.org/api_docs/python/tf/function for  more details.
1/1 ━━━━━━━━━━━━━━━━━━━━ 0s 433ms/step
C:\Users\saipa\.vscode\sem6\Predictive Maintenance Dashboard.py:69: DeprecationWarning:
 and website is working perfectly
 taking employee auntication 
 real time data showing then alret system and Graphs and maintenance Scheduling for next_maintenance
   

   ##### now performance metric 
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

output 
PS C:\Users\saipa\.vscode\sem6> & C:/Users/saipa/AppData/Local/Programs/Python/Python310/python.exe "c:/Users/saipa/.vscode/sem6/performance metrics.py"
2025-03-15 23:38:48.004073: I tensorflow/core/util/port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
2025-03-15 23:38:49.895175: I tensorflow/core/util/port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
2025-03-15 23:38:53.728353: I tensorflow/core/platform/cpu_feature_guard.cc:210] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 AVX512F AVX512_VNNI FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
3/3 ━━━━━━━━━━━━━━━━━━━━ 1s 165ms/step
3/3 ━━━━━━━━━━━━━━━━━━━━ 0s 17ms/step
✅ Accuracy: 0.7778
🎯 Precision: 0.0714
📈 Recall: 0.1250
⚖️ F1-Score: 0.0909
📉 Mean Squared Error (MSE): 0.2222
⏳ Latency: 0.1194 seconds

PS C:\Users\saipa\.vscode\sem6> & C:/Users/saipa/AppData/Local/Programs/Python/Python310/python.exe "c:/Users/saipa/.vscode/sem6/performance metrics.py"
2025-03-03 19:06:34.480398: I tensorflow/core/util/port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
2025-03-03 19:06:35.809985: I tensorflow/core/util/port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
2025-03-03 19:06:38.572081: I tensorflow/core/platform/cpu_feature_guard.cc:210] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 AVX512F AVX512_VNNI FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
3/3 ━━━━━━━━━━━━━━━━━━━━ 1s 168ms/step
3/3 ━━━━━━━━━━━━━━━━━━━━ 0s 19ms/step
✅ Accuracy: 0.8111
🎯 Precision: 0.0714
📈 Recall: 0.2000
⚖️ F1-Score: 0.1053
📉 Mean Squared Error (MSE): 0.1889
⏳ Latency: 0.1053 seconds
PS C:\Users\saipa\.vscode\sem6> 