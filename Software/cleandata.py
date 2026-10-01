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
