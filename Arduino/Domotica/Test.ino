#include "ThingSpeakCustom.h"
#include <Client.h>
#include <WiFi.h>

//----------------  Fill in your credentails   ---------------------
char ssid[] = "XXXXX";     // your network SSID (name) 
char pass[] = "password; // your network password
//------------------------------------------------------------------

WiFiClient  client;

unsigned long ChannelNumber = 123456;
unsigned int FieldLight = 1;
const char * ReadAPIKey = "XXXXXXXXXXXXX";
const int Led = 1;
const int LED_BUILTIN = 2;

//------------------------------------------------------------------



void setup() {
 //Initialize serial and wait for port to open:
 Serial.begin(9600);
 while (!Serial) {
   ; // wait for serial port to connect. Needed for native USB port only
 }

 WiFi.mode(WIFI_STA);  
 ThingSpeak.begin(client);
 pinMode(LED_BUILTIN,OUTPUT);
 pinMode(Led, OUTPUT); 
}



void loop() {

 int statusCode = 0;
 
 // Connect or reconnect to WiFi
 if(WiFi.status() != WL_CONNECTED){
   Serial.print("Attempting to connect wifi");
   while(WiFi.status() != WL_CONNECTED){
     WiFi.begin(ssid, pass);
     Serial.print(".");
     delay(5000);     
   } 
   Serial.println("\nConnected");
 }
 

 

 // Read in field 4 of the public channel recording the temperature
int light = ThingSpeak.readIntField (ChannelNumber, FieldLight, ReadAPIKey);

 // Check the status of the read operation to see if it was successful
 statusCode = ThingSpeak.getLastReadStatus();
 if(statusCode == 200){ 
   if(light){
    digitalWrite(LED_BUILTIN,HIGH);
    Serial.print("led on");
   }
    
   else{
    digitalWrite(LED_BUILTIN,LOW);
    Serial.println("led off");
   }
    
 }
 else{
   Serial.println("Problem reading channel. HTTP error code " + String(statusCode)); 
 }
 
 delay(150); 
 
}
