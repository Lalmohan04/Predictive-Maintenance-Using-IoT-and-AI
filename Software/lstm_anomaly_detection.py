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
