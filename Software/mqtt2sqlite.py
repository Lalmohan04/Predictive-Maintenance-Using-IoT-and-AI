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
