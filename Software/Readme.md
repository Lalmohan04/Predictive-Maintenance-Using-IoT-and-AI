**Predictive Maintenance System using IoT & AI**  

## **📌 Overview**  
This project implements a **Predictive Maintenance System** using **ESP8266, DHT11, MPU6050, MQTT, SQLite, and AI models (Isolation Forest & LSTM)**.  

✅ **Monitors** → Temperature, Humidity, and Vibration.  
✅ **Detects Anomalies** → Using AI (Isolation Forest & LSTM).  
✅ **Predicts Failures** → Helps in maintenance scheduling.  
✅ **Live Dashboard** → Displays real-time data & alerts.  

---

## **🛠 Hardware Setup**  
### **1️⃣ Required Components**  
| Component              | Description |
| ESP8266                | Microcontroller for IoT connectivity |
| DHT11                  | Temperature & Humidity Sensor |
| MPU6050                | Accelerometer & Gyroscope (Vibration Monitoring) |
| DC Motor (Optional)    | For simulating real-world machine vibrations |
| Jumper Wires           | For circuit connections |
| Breadboard             | For prototyping |

### **2️⃣ Wiring & Connections**  
**ESP8266 Pinout Configuration:**
```
DHT11    -> VCC to 3.3V, GND to GND, Data to D4 (GPIO2)
MPU6050  -> VCC to 3.3V, GND to GND, SCL to D1 (GPIO5), SDA to D2 (GPIO4)
```
(Insert an **image of the connection diagram** here for reference.)

---

## **📦 Software Setup**  
### **1️⃣ Required Software & Tools**  
| Software                  | Purpose |
| **Arduino IDE (1.8.19)**  | Upload code to ESP8266 |
| **Python 3.9+**           | Runs data processing & AI scripts |
| **VS Code**               | Recommended for running Python scripts |
| **SQLite 3.41+**          | Stores sensor data |
| **HiveMQ (MQTT Broker)**  | Transfers data between ESP8266 & PC |
| **Streamlit**             | Dashboard for real-time monitoring |


### **2️⃣ Install Arduino IDE & ESP8266 Board**  
1. **Download & Install Arduino IDE (1.8.19)** from [Arduino Website](https://www.arduino.cc/en/software).  
2. **Add ESP8266 Board Support**:  
   - Open **Arduino IDE** → **File** → **Preferences**.  
   - Add this URL in **Additional Board Manager URLs**:  
     ```
     http://arduino.esp8266.com/stable/package_esp8266com_index.json
     ```
   - Go to **Tools** → **Board** → **Boards Manager**.  
   - Search for **ESP8266** and install **version 2.7.4**.  

---

### **3️⃣ Install Required Libraries in Arduino IDE**  
Go to **Sketch** → **Include Library** → **Manage Libraries**, then install:  
- **ESP8266WiFi** (Built-in)  
- **PubSubClient** (For MQTT Communication)  
- **Adafruit MPU6050** (For Vibration Sensor)  
- **DHT Sensor Library** (For DHT11)  

---

## **🚀 Uploading ESP8266 Code**  
📌 **File:** `espmqtt_main.ino`  
📌 **Purpose:** Reads **sensor data**, connects to **MQTT**, and transmits values.  

### **🔹 Steps to Upload Code**  
1. Connect **ESP8266 via USB**.  
2. Open `espmqtt_main.ino` in **Arduino IDE**.  
3. Modify WiFi & MQTT Credentials:  
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* mqtt_server = "YOUR_MQTT_BROKER";
   ```
4. Select **Board** → `NodeMCU 1.0 (ESP-12E Module)`.  
5. Select **Port** → (Your ESP8266 COM Port).  
6. Click **Upload** ✅.  

---

## **📡 MQTT & Database Setup**  
### **1️⃣ Install Required Python Libraries**  
Open a terminal in **VS Code** and run:  
```sh
pip install paho-mqtt sqlite3 pandas numpy scikit-learn tensorflow streamlit
```

### **2️⃣ Run MQTT to SQLite Script**  
📌 **File:** `mqtt2sqlite.py`  
📌 **Purpose:** Captures sensor data from MQTT and stores it in SQLite.  

#### **🔹 How to Run**  
```sh
python mqtt2sqlite.py
```

#### **📝 Expected Output**
```sh
Connected to MQTT Broker
Subscribed to Topic: sensor/data
Received Data: {"temperature": 25.3, "humidity": 60, "vibration": 0.01}
Data stored in SQLite: sensor_data.db
```

#### **📂 File Created**  
- **`sensor_data.db`** → Stores sensor values.

---

## **📊 AI-Based Anomaly Detection**  
### **1️⃣ Run Isolation Forest Model**  
📌 **File:** `IFM.py`  
📌 **Purpose:** Detects **anomalies** in the sensor data.  

#### **🔹 How to Run**  
```sh
python IFM.py
```

#### **📂 File Created**  
- **`anomaly_results.csv`** → Stores detected anomalies.  

---

### **2️⃣ Data Preprocessing for LSTM Model**  
📌 **File:** `cleandata.py`  
📌 **Purpose:** Prepares sensor data for **LSTM-based anomaly detection**.  

#### **🔹 How to Run**  
```sh
python cleandata.py
```

#### **📂 File Created**  
- **`cleaned_data.csv`** → Cleaned dataset for LSTM training.  

---

### **3️⃣ LSTM Model for Anomaly Prediction**  
📌 **File:** `lstm_anomaly_detection.py`  
📌 **Purpose:** Uses **LSTM Neural Network** to predict future failures.  

#### **🔹 How to Run**  
```sh
python lstm_anomaly_detection.py
```

#### **📂 File Created**  
- **`lstm_model.h5`** → Trained LSTM model.  
- **`lstm_predictions.csv`** → Predicted anomalies.  

---

## **📊 Real-Time Dashboard (Visualization & Alerts)**  
📌 **File:** `Predictive_Maintenance_Dashboard.py`  
📌 **Purpose:** Displays **real-time sensor data & alerts** using **Streamlit**.  

#### **🔹 How to Run**  
```sh
streamlit run Predictive_Maintenance_Dashboard.py
```

#### **🌍 Where It Runs?**  
- **Runs in Web Browser**  
- **URL:** `http://localhost:8501`  

---

## **📂 Folder Structure**
```
📂 Predictive_Maintenance
├── 📂 Arduino_Code
│   ├── espmqtt_main.ino (ESP8266 Code)
│
├── 📂 Python_Code
│   ├── mqtt2sqlite.py (MQTT to Database)
│   ├── IFM.py (Isolation Forest Model)
│   ├── cleandata.py (Data Preprocessing)
│   ├── lstm_anomaly_detection.py (LSTM Model)
│   ├── Predictive_Maintenance_Dashboard.py (Streamlit UI)
│
├── 📂 Database
│   ├── sensor_data.db (SQLite Database)
│
└── README.md (This Documentation)
```

---

## **✅ Final Summary**
- **Step 1:** Upload `main.cpp` to ESP8266 ✅  
- **Step 2:** Run `mqtt2sqlite.py` to store sensor data ✅  
- **Step 3:** Run `IFM.py` to detect anomalies ✅  
- **Step 4:** Preprocess data with `cleandata.py` ✅  
- **Step 5:** Train & predict anomalies using `lstm_anomaly_detection.py` ✅  
- **Step 6:** Run `Predictive_Maintenance_Dashboard.py` for visualization ✅  

📌 **This guide ensures a smooth setup!** 🚀  
💯 **Copy-paste in VS Code or GitHub README without issues.** 🔥  

Let me know if you need modifications! 👍