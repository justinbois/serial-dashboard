const int voltagePin = A0;

const int redLEDPin = 6;
const int greenLEDPin = 2;

const int HANDSHAKE = 0;
const int REQUEST = 1;
const int RED_LED_ON = 2;
const int RED_LED_OFF = 3;
const int GREEN_LED_ON = 4;
const int GREEN_LED_OFF = 5;

const int ON_REQUEST = 6;
const int STREAM = 7;
const int READ_DAQ_DELAY = 8;

const int TOGGLE_SINE_WAVE = 9;

const int HANDSHAKE_ASCII = 48;
const int REQUEST_ASCII = 49;
const int RED_LED_ON_ASCII = 50;
const int RED_LED_OFF_ASCII = 51;
const int GREEN_LED_ON_ASCII = 52;
const int GREEN_LED_OFF_ASCII = 53;

const int ON_REQUEST_ASCII = 54;
const int STREAM_ASCII = 55;
const int READ_DAQ_DELAY_ASCII = 56;

const int TOGGLE_SINE_WAVE_ASCII = 57;

String daqDelayStr;

int inByte = 0;
int daqMode = ON_REQUEST;
int daqDelay = 100;

unsigned long timeOfLastDAQ = 0;

bool showSineWave = true;


unsigned long printOutput() {
  String outstr;
  
  // read value from analog pin
  int value = analogRead(voltagePin);

  // Time of acquisition
  unsigned long timeMilliseconds = millis();

  // Generate sine wave
  int sineWave = (int) ((1.0 + sin(((float) timeMilliseconds) / 1000.0 * 2 * PI)) / 2.0 * 1023.0);

  // Write the result
  if (Serial.availableForWrite()) {
    if (showSineWave) {
      outstr = String(String(timeMilliseconds, DEC) + "," + String(value, DEC) + "," + String(sineWave, DEC));
    }
    else {
      outstr = String(String(timeMilliseconds, DEC) + "," + String(value, DEC) + ",");        
    }
    Serial.println(outstr);
  }

  // Return the time of acquisition
  return timeMilliseconds;
}


void setup() {
  // Set LEDs to off
  pinMode(redLEDPin, OUTPUT);
  pinMode(greenLEDPin, OUTPUT);
  digitalWrite(redLEDPin, LOW);
  digitalWrite(greenLEDPin, LOW);

  // initialize serial communication
  Serial.begin(115200);
}


void loop() {
  // If we're auto-transferring data (streaming mode)
  if (daqMode == STREAM) {
    if (millis() - timeOfLastDAQ >= daqDelay) {
      timeOfLastDAQ = printOutput();
    }
  }

  // Check if data has been sent to Arduino and respond accordingly
  if (Serial.available() > 0) {
    // Read in request
    inByte = Serial.read();

    // Handshake
    if (inByte == HANDSHAKE | inByte == HANDSHAKE_ASCII){
      if (Serial.availableForWrite()) {
          Serial.println("Handshake message received.");
      }
    }

    // If data is requested, fetch it and write it
    else if (inByte == REQUEST | inByte == REQUEST_ASCII) printOutput();

    // Switch daqMode
    else if (inByte == ON_REQUEST | inByte == ON_REQUEST_ASCII) daqMode = ON_REQUEST;
    else if (inByte == STREAM | inByte == STREAM_ASCII) daqMode = STREAM;

    // Read in DAQ delay
    else if (inByte == READ_DAQ_DELAY | inByte == READ_DAQ_DELAY_ASCII) {
      while (Serial.available() == 0) ;
      daqDelayStr = Serial.readStringUntil('x');
      daqDelay = daqDelayStr.toInt();
    }

    // Toggle display of the sine wave
    else if (inByte == TOGGLE_SINE_WAVE | inByte == TOGGLE_SINE_WAVE_ASCII) {
      showSineWave = showSineWave ? false : true;
    }

    // else, turn LEDs on or off
    else if (inByte == RED_LED_ON | inByte == RED_LED_ON_ASCII) digitalWrite(redLEDPin, HIGH);
    else if (inByte == RED_LED_OFF | inByte == RED_LED_OFF_ASCII) digitalWrite(redLEDPin, LOW);
    else if (inByte == GREEN_LED_ON | inByte == GREEN_LED_ON_ASCII) digitalWrite(greenLEDPin, HIGH);
    else if (inByte == GREEN_LED_OFF | inByte == GREEN_LED_OFF_ASCII) digitalWrite(greenLEDPin, LOW);
  }
}