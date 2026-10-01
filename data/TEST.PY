# import sqlite3
# import pandas as pd

# # Connect to the database
# conn = sqlite3.connect("sensor_data.db")
# cursor = conn.cursor()

# # Fetch relevant data (temperature, humidity, vibration)
# query = """
# SELECT timestamp,
#        CASE 
#            WHEN sensor_type LIKE 'temperature%' THEN 'temperature'
#            WHEN sensor_type LIKE 'humidity%' THEN 'humidity'
#            WHEN sensor_type LIKE 'acceleration_a%' THEN 'vibration'
#        END AS sensor_type,
#        CAST(value AS FLOAT) AS value
# FROM sensor_data
# WHERE sensor_type LIKE 'temperature%' 
#    OR sensor_type LIKE 'humidity%' 
#    OR sensor_type LIKE 'acceleration_a%'
# ORDER BY timestamp;
# """

# df = pd.read_sql_query(query, conn)
# conn.close()

# # Save cleaned data for LSTM training
# df.to_csv("clean_sensor_data.csv", index=False)
# print("✅ Data cleaned and saved as clean_sensor_data.csv")
import sqlite3

conn = sqlite3.connect("anomalies.db")  # Make sure this is the correct path
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM anomalies")
count = cursor.fetchone()[0]

print(f"Total rows in sensor_data: {count}")

cursor.execute("SELECT * FROM anomalies LIMIT 5  ")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
