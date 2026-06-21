/*
  ESP-NOW Demo - Receive
  esp-now-demo-rcv.ino
  Reads data from Initiator
  
  DroneBot Workshop 2022
  https://dronebotworkshop.com
*/

// Include Libraries
#include <esp_now.h>
#include <WiFi.h>

// Estrutura da mensagem enviada pelo transmissor (load_cell_RF)
typedef struct struct_message {
  float timestamp_s;       // Timestamp da coleta [s]
  float load_cell_1_g;     // Massa célula 1 [g]
  float load_cell_2_g;     // Massa célula 2 [g]
  float thermocouple_1_c;  // Temperatura termopar 1 [°C]
  float thermocouple_2_c;  // Temperatura termopar 2 [°C]
} struct_message;

struct_message myData;

void OnDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len) {
  if (len != sizeof(myData)) {
    Serial.printf("Tamanho inesperado: %d bytes (esperado %d)\n", len, (int)sizeof(myData));
    return;
  }
  memcpy(&myData, incomingData, sizeof(myData));
  Serial.printf("%.3fs  LC1:%7.1fg  LC2:%7.1fg  TC1:%5.1fC  TC2:%5.1fC\n",
    myData.timestamp_s,
    myData.load_cell_1_g,
    myData.load_cell_2_g,
    myData.thermocouple_1_c,
    myData.thermocouple_2_c);
}

void setup() {
  // Set up Serial Monitor
  Serial.begin(115200);
  
  // Set ESP32 as a Wi-Fi Station
  WiFi.mode(WIFI_STA);

  // Initilize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  
  // Register callback function
  esp_now_register_recv_cb(OnDataRecv);
}
 
void loop() {

}