#include <Wire.h>           // Library for I2C communication
#include <DHT.h>            // Library for DHT sensor
#include <ESP8266WiFi.h>    // ESP8266 WiFi Library
#include <PubSubClient.h>   // MQTT Client Library
#include <math.h>           // Library for mathematical operations (sqrt())

// WiFi Credentials
const char* ssid = "WIFI";          // WiFi SSID (Network Name)
const char* password = "******"; // WiFi Password

// MQTT Broker Credentials
const char* mqtt_server = "4fa8f8*******cc25a*****1e6.s1.eu.hivemq.cloud"; // MQTT Broker Address
const int mqtt_port = 8883;  // Secure MQTT Port
const char* mqtt_user = "Myiot"; // MQTT Username
const char* mqtt_password = "******"; // MQTT Password

// MQTT Topics for publishing sensor data
const char* topic_temp = "sensor/temperature";  // Temperature topic
const char* topic_humidity = "sensor/humidity"; // Humidity topic
const char* topic_vibration = "sensor/vibration"; // Vibration topic

// DHT11 Sensor Configuration
#define DHTPIN D4         // GPIO Pin connected to DHT11
#define DHTTYPE DHT11     // Define the sensor type (DHT11)
DHT dht(DHTPIN, DHTTYPE); // Create DHT object

// MPU6050 Configuration
const int MPU_ADDR = 0x68;  // I2C address of MPU6050
int16_t AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ;  // Variables to store sensor readings

// WiFi & MQTT Clients
WiFiClientSecure espClient;   // Secure WiFi Client for SSL/TLS connection
PubSubClient client(espClient); // MQTT Client

// Function to Connect to WiFi
void setup_wifi() {
    delay(10);
    Serial.println("Connecting to WiFi...");
    WiFi.begin(ssid, password);  // Start connecting to WiFi

    // Wait until WiFi is connected
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi Connected.");  // Confirm WiFi connection
}

// Function to Reconnect to MQTT Broker if Disconnected
void reconnect_mqtt() {
    while (!client.connected()) {  // Check if MQTT is connected
        Serial.print("Connecting to MQTT...");
        if (client.connect("ESP8266Client", mqtt_user, mqtt_password)) { // Try connecting
            Serial.println("Connected.");
        } else {
            Serial.print("Failed, rc=");  // Print error code if connection fails
            Serial.print(client.state());
            Serial.println(" Trying again in 5 seconds...");
            delay(5000); // Wait before retrying
        }
    }
}

// Function to Initialize MPU6050 Manually
void initMPU6050() {
    Wire.beginTransmission(MPU_ADDR);
    
    // Check if MPU6050 is responding
    if (Wire.endTransmission() == 0) {
        Serial.println("MPU6050 is connected!");
    } else {
        Serial.println("MPU6050 NOT found! Check connections.");
        while (1);  // Halt execution if MPU6050 is not detected
    }

    // Wake up MPU6050 (reset sleep mode)
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x6B);  // Power management register
    Wire.write(0);     // Set to 0 to wake up
    Wire.endTransmission(true);
}

// Setup Function (Runs Once at Startup)
void setup() {
    Serial.begin(115200);  // Initialize Serial Monitor
    Wire.begin();  // Initialize I2C communication
    dht.begin();   // Initialize DHT11 sensor
    setup_wifi();  // Connect to WiFi

    espClient.setInsecure();  // Allow insecure connections for MQTT over SSL
    client.setServer(mqtt_server, mqtt_port);  // Set MQTT broker details

    initMPU6050();  // Initialize MPU6050 sensor
}

// Function to Read and Publish Sensor Data to MQTT
void publish_sensor_data() {
    // Read Temperature & Humidity from DHT11
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    // Read Acceleration and Gyroscope Data from MPU6050
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x3B);  // Start reading at register 0x3B (Acceleration X)
    Wire.endTransmission(false);
    Wire.requestFrom(MPU_ADDR, 14, true);  // Request 14 bytes from MPU6050

    // Read acceleration, temperature, and gyroscope data
    AcX = Wire.read() << 8 | Wire.read();
    AcY = Wire.read() << 8 | Wire.read();
    AcZ = Wire.read() << 8 | Wire.read();
    Tmp = Wire.read() << 8 | Wire.read();
    GyX = Wire.read() << 8 | Wire.read();
    GyY = Wire.read() << 8 | Wire.read();
    GyZ = Wire.read() << 8 | Wire.read();

    // Compute Vibration Intensity (Magnitude)
    float vibration = sqrt(AcX * AcX + AcY * AcY + AcZ * AcZ + GyX * GyX + GyY * GyY + GyZ * GyZ) / 1000.0;

    // Convert Sensor Data to JSON Format
    String json_temp = "{\"temperature\": " + String(temperature) + "}"; // Temperature JSON
    String json_humidity = "{\"humidity\": " + String(humidity) + "}";  // Humidity JSON
    String json_vibration = "{\"vibration\": " + String(vibration) + "}";  // Vibration JSON

    // Publish Data to MQTT Topics
    client.publish(topic_temp, json_temp.c_str());      // Publish Temperature
    client.publish(topic_humidity, json_humidity.c_str());  // Publish Humidity
    client.publish(topic_vibration, json_vibration.c_str());  // Publish Vibration Data

    Serial.println("✅ Published Sensor Data.");  // Log confirmation message
}

// Main Loop (Runs Continuously)
void loop() {
    if (!client.connected()) {  // Check MQTT Connection
        reconnect_mqtt();       // Reconnect if disconnected
    }
    client.loop();  // Maintain MQTT connection
    publish_sensor_data();  // Read and publish sensor data
    delay(5000);  // Wait 5 seconds before sending the next data update
}
