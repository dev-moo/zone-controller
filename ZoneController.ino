
#include <SoftwareSerial.h>

/*Settings to Control Zone Controller*/

//Pins
const byte ZONE1_PIN = 7;
const byte ZONE2_PIN = 6;
const byte ZONE3_PIN = 5;
const byte ZONE4_PIN = 4;
const byte ZONE5_PIN = 3;

const byte ZONE1_CODE = '1';
const byte ZONE2_CODE = '2';
const byte ZONE3_CODE = '3';
const byte ZONE4_CODE = '4';
const byte ZONE5_CODE = '5';



/*Settings to Probe Zone Controller*/

SoftwareSerial ProbeSerial(10, 11, true); // RX, TX, Invert

const int NUMZONES = 6;
const int PACKETLEN = 8;
const byte STARTSEQ[2] = {0x25, 0x21};


/* Operations */

const byte GET = 'G';
const byte SET = 'S';
const byte CHECK = 'C';


/* Settings to use Button 6 for our own purposes */

const byte BUTTON6 = 2;
const byte LED = 13;


/* Global and Other Variables */
volatile boolean flag;
byte input = 0;
const int PULSE_DELAY = 50;



// Interrupt Service Routine (ISR) to listen for BUTTON6 press
void switchPressed () {

  if (!flag) {
    flag = true;
  }

}




//Get individual 'packets' sent on zone controller serial link
boolean GetPacket(byte *buf, int maxrecursions) {

  //Prevent infinite loop
  if (maxrecursions > 10) {
    maxrecursions = 10;
  } else if (maxrecursions < 0) {
    return false;
  }
  maxrecursions--;

  //Flush serial buffer
  ProbeSerial.flush();

  int maxloops = 10;
  int index = 0;
  boolean packetreceived = true;


  //Wait for some data to be received
  while (!ProbeSerial.available()) {

    //Prevent getting stuck in loop
    if (maxloops < 0) {
      return false;
    }
    maxloops--;

    delay(25);

  }

  //Read serial data into buffer
  while (ProbeSerial.available()) {

    *(buf + index) = ProbeSerial.read();

    if (index >= PACKETLEN) {
      break; //Break from loop if num bytes received exceeds expected packet length
    }
    index++;
    delay(1);

  }

  //Test data has a valid start sequence
  for (int s = 0; s < sizeof(STARTSEQ); s++) {

    if (*(buf + s) != STARTSEQ[s]) {
      packetreceived = false;
      break;
    }
  }

  //If invalid packet received recurse function
  if (!packetreceived) {

    //Start again
    if (GetPacket(buf, maxrecursions)) {
      return true;
    } else {
      return false;
    }
  }

  return true;

}


//Probe Serial link to Zone Controller and get the info we need
boolean ProbeZoneContoller() {

  byte packetBuffer[PACKETLEN];
  byte sendBuffer[PACKETLEN * NUMZONES];
  int index = 0;
  int maxtries = 5;

  //Get status of each zone from zone controller serial line
  for (int y = 0; y < NUMZONES; y++) {

    if (!GetPacket(packetBuffer, maxtries)) {
      return false;
    }

    for (int x = 0; x < PACKETLEN; x++) {

      sendBuffer[index] = packetBuffer[x];
      index++;

    }
  }


  for (int w = 0; w < (PACKETLEN * NUMZONES); w++) {

    /*FOR TESTING
    if(w!= 0 && w%PACKETLEN == 0){
          Serial.println("");
      }*/

    Serial.print(sendBuffer[w], HEX);

    //Serial.print(" ");FOR TESTING

  }

  Serial.println("");

  return true;

}


//Send pulse to a pin (press button on zone controller)
void PressButton(byte button) {

  digitalWrite (button, HIGH);
  delay(PULSE_DELAY);
  digitalWrite (button, LOW);
  delay(PULSE_DELAY);

}


//Receive instructions from USB to press buttons
void ReceiveCommand() {

  byte in;

  //Read up to 32 bytes from Serial input
  for (int i = 0; i < 32; i++) {

    //Wait for serial data to become available
    for (int j = 0; j < 20; j++) {
      if (Serial.available()) {
        break;
      }
      delay(1);
    }

    in = Serial.read();

    if (in >= ZONE1_CODE && in <= ZONE5_CODE) {

      switch (in) {
        case ZONE1_CODE:
          PressButton(ZONE1_PIN);
          break;
        case ZONE2_CODE:
          PressButton(ZONE2_PIN);
          break;
        case ZONE3_CODE:
          PressButton(ZONE3_PIN);
          break;
        case ZONE4_CODE:
          PressButton(ZONE4_PIN);
          break;
        case ZONE5_CODE:
          PressButton(ZONE5_PIN);
          break;
      }

    } else {
      break;
    }
  }
}




void setup () {

  //Init all the pins
  pinMode(ZONE1_PIN, OUTPUT);
  pinMode(ZONE2_PIN, OUTPUT);
  pinMode(ZONE3_PIN, OUTPUT);
  pinMode(ZONE4_PIN, OUTPUT);
  pinMode(ZONE5_PIN, OUTPUT);

  pinMode(LED, OUTPUT);  //Gimmiky feedback
  pinMode(BUTTON6, INPUT);  //Use button 6 for input

  attachInterrupt(digitalPinToInterrupt(BUTTON6), switchPressed, FALLING);  // attach interrupt handler to 'BUTTON6'

  //Serial links
  Serial.begin(9600);
  ProbeSerial.begin(9600);

  Serial.println("OK");

}

//Main loop
void loop () {

  //Get input/instructions from Serial (USB) port
  if (Serial.available()) {

    input = Serial.read();

    //Probe Zone Controller for current status
    if (input == GET) {

      if (!ProbeZoneContoller()) {
        Serial.println("FAILED");
      }

      //Control Zones
    } else if (input == SET) {
      //Serial.print(Serial.available());
      ReceiveCommand();

      //Check this service is alive
    } else if (input == CHECK) {
      Serial.println("OK");
    }

    input = NULL; //Clear variable

  }

  //If BUTTON6 Pressed
  if (flag) {

    digitalWrite(LED, HIGH);
    Serial.println("ButtonPressed");
    delay(200); //Eliminate switch bounce
    digitalWrite(LED, LOW);
    flag = false;

  }
}
