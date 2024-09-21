#include <ESP8266WiFi.h>      // Include WiFi library for ESP8266
#include <DHT.h>              // Include DHT sensor library

// WiFi credentials
const char* ssid = "your-SSID";
const char* password = "your-PASSWORD";

// ThingSpeak details
const char* host = "api.thingspeak.com";
const char* apiKey = "your-THINGSPEAK-API-KEY";

// DHT sensor settings
#define DHTPIN D4           // DHT sensor is connected to pin D4
#define DHTTYPE DHT11       // DHT 11 sensor (can use DHT22)
DHT dht(DHTPIN, DHTTYPE);

// Timer settings
unsigned long lastUpdate = 0;
const long interval = 20000;  // Update interval of 20 seconds

void setup() {
  Serial.begin(115200);
  dht.begin();

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - lastUpdate >= interval) {
    lastUpdate = currentMillis;

    // Read temperature and humidity from DHT sensor
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();

    if (isnan(humidity) || isnan(temperature)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println(" °C");
    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");

    // Send data to ThingSpeak
    if (WiFi.status() == WL_CONNECTED) {
      WiFiClient client;
      const int httpPort = 80;
      if (!client.connect(host, httpPort)) {
        Serial.println("Connection to ThingSpeak failed");
        return;
      }

      // Create the HTTP request string
      String url = "/update?api_key=" + String(apiKey);
      url += "&field1=" + String(temperature);
      url += "&field2=" + String(humidity);

      client.print(String("GET ") + url + " HTTP/1.1\r\n" +
                   "Host: " + host + "\r\n" +
                   "Connection: close\r\n\r\n");

      Serial.println("Data sent to ThingSpeak!");
    }
  }
}
