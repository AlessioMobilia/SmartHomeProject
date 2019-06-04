#include <ThingSpeak.h>
#include <Client.h>
#include <WiFi.h>

//----------------  Fill in your credentails   ---------------------
char ssid[] = "XXXXXX"; // your network SSID (name) 
char pass[] = "password1234"; // your network password
//------------------------------------------------------------------

WiFiClient  client;

unsigned long ChannelNumber = 123456;
unsigned int FieldLight = 1;
const char * ReadAPIKey = "XXXXXXXXXXXXXXXXX";
const char * WriteAPIKey = "XXXXXXXXXXXXXXXX";
const int MAX_ATTEMPT = 15; //limite massimo di tentativi di aggiornare il canale
const int BUTTON = 12;
const int ERRORE = 14;
const int LED_BUILTIN = 2;
const int LIGHT = 13;

int buttonState = 0;
int lightState = 0;
int lastButtonState = 0;
bool er = false;
int number = 0;
int statusCode = 0;
int attempt =0;


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
 pinMode(LIGHT,OUTPUT);
 pinMode(ERRORE,OUTPUT);
 pinMode(BUTTON,INPUT);
}



void loop() {
  // Connect or reconnect to WiFi
 if(WiFi.status() != WL_CONNECTED){
   digitalWrite(ERRORE, HIGH);
   Serial.print("Attempting to connect wifi");
   while(WiFi.status() != WL_CONNECTED){
     WiFi.begin(ssid, pass);
     Serial.print(".");
     delay(5000);  
   } 
   Serial.println("\nConnected");
 }
 

 buttonState = digitalRead(BUTTON);
 
 if ((buttonState == HIGH)&&(buttonState!=lastButtonState)) {
    Serial.println("Button Pressed");
    // turn LED on:
    if(lightState == LOW){
      digitalWrite(LIGHT, HIGH);
      lightState = HIGH;
      number = 1;
    }
    else {
      digitalWrite(LIGHT, LOW);
      lightState = LOW;
      number = 0;
    }
    //upload status
    do{
      attempt+=1;
      Serial.print("Tentativo di aggiornare il canale n.");
      Serial.println(attempt);
      digitalWrite(ERRORE, HIGH);
      int x = ThingSpeak.writeField(ChannelNumber, FieldLight, number, WriteAPIKey);
      // Check the return code
      if(x == 200){
        Serial.println("Channel update successful.");
        er=false;
        digitalWrite(ERRORE, LOW);
        
      }
      else{
        Serial.println("Problem updating channel. HTTP error code " + String(x));
        digitalWrite(ERRORE, HIGH);
        er=true;
      }
    }while((er)&&(attempt<MAX_ATTEMPT)); // riprova a inviare il comando se c'è stato un errore
    attempt=0;
  } 
  else {
   // Read in field 4 of the public channel recording the temperature
  int light = ThingSpeak.readIntField (ChannelNumber, FieldLight, ReadAPIKey);

  // Check the status of the read operation to see if it was successful
  statusCode = ThingSpeak.getLastReadStatus();
  if(statusCode == 200){ 
   if(light){
    lightState=HIGH;
    digitalWrite(LIGHT,HIGH);
    Serial.println("led on");
    digitalWrite(ERRORE, LOW);
   }
    
   else{
    lightState=LOW;
    digitalWrite(LIGHT,LOW);
    Serial.println("led off");
    digitalWrite(ERRORE, LOW);
   }
    
  }
  else{
   digitalWrite(ERRORE, HIGH);
   Serial.println("Problem reading channel. HTTP error code " + String(statusCode)); 
  }
  
  //delay(150); 

  }
  lastButtonState = buttonState;

 
} 
