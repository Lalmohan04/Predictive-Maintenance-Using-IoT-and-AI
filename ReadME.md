# Predictive Maintenance Using IoT and AI

## Intelligent Equipment Monitoring, Anomaly Detection & Failure Prediction

A complete **IoT and AI-based Predictive Maintenance System** that collects real-time temperature, humidity, and vibration data from industrial equipment using an **ESP8266**, transmits the data through **MQTT**, stores it in **SQLite**, and applies machine learning models for anomaly detection and Remaining Useful Life (RUL) prediction.

The system combines **IoT sensing, MQTT communication, data storage, machine learning, and real-time dashboard visualization** into an end-to-end predictive maintenance workflow.

---

## Project Overview

Traditional maintenance approaches can result in unexpected equipment failures, unnecessary servicing, downtime, and increased maintenance costs.

This project implements a data-driven predictive maintenance system that continuously monitors equipment conditions and analyzes sensor readings to identify abnormal behavior and predict potential failures.

The system uses:

- **ESP8266 NodeMCU** for IoT data acquisition
- **DHT11** for temperature and humidity monitoring
- **MPU6050** for vibration monitoring
- **MQTT / HiveMQ Cloud** for real-time communication
- **SQLite** for sensor-data storage
- **Isolation Forest** for anomaly detection
- **LSTM** for Remaining Useful Life (RUL) prediction
- **Streamlit** for dashboard visualization

The project report describes the complete workflow from sensor data collection through AI-based analysis and dashboard visualization. 

---

## System Architecture

```text
+------------------------+
|      ESP8266 NodeMCU   |
|                        |
|  DHT11 + MPU6050       |
|  Temperature           |
|  Humidity              |
|  Vibration             |
+-----------+------------+
            |
            | MQTT
            v
+------------------------+
|     HiveMQ Cloud       |
|      MQTT Broker       |
+-----------+------------+
            |
            v
+------------------------+
|    Python Processing   |
|     mqtt2sqlite.py     |
+-----------+------------+
            |
            v
+------------------------+
|     SQLite Database    |
|    sensor_data.db      |
+-----------+------------+
            |
            v
+------------------------+
|      AI / ML Layer     |
|                        |
|  Isolation Forest      |
|  Anomaly Detection     |
|                        |
|  LSTM                  |
|  RUL Prediction        |
+-----------+------------+
            |
            v
+------------------------+
|   Streamlit Dashboard  |
|                        |
| Sensor Trends          |
| Anomaly Alerts         |
| Predictions            |
+------------------------+