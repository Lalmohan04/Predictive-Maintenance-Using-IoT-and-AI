import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("sensor_data.db")
cursor = conn.cursor()

# Enable WAL mode
cursor.execute("PRAGMA journal_mode=WAL;")
conn.commit()
conn.close()

print("✅ WAL mode enabled successfully for sensor_data.db!")
