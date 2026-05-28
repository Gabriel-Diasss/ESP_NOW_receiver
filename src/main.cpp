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
  char labelA[32];     // "Filtered Mass:"
  float filteredMass;  // Massa filtrada em gramas
  char labelC[32];     // "Raw Mass:"
  float rawMass;       // Massa bruta em gramas
} struct_message;

struct_message myData;

void OnDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len) {
  memcpy(&myData, incomingData, sizeof(myData));
  Serial.print("Data received: ");
  Serial.println(len);
  Serial.print(myData.labelA);
  Serial.print(" ");
  Serial.print(myData.filteredMass, 3);
  Serial.println(" g");
  Serial.print(myData.labelC);
  Serial.print(" ");
  Serial.print(myData.rawMass, 3);
  Serial.println(" g");
  Serial.println();
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