int redPin = 13;

// digital pins

int onPin = 6;
int lwPin = 5;
int mwPin = 4;
int kwPin = 3;
int ukwPin = 2;

int onVal = 0;
int lwVal = 0;
int mwVal = 0;
int kwVal = 0;
int ukwVal = 0;

// analog pins
// Potis are 0-25kOhm meassured between 2nd and 3rd pin

int volPin = A1;
int volVal = 0;
int volReadMin = 300;
int volReadMax = 988;

int trebPin = A2;
int trebVal = 0;
int trebReadMin = 2;
int trebReadMax = 984;

// pins for meassuring the capacitator

int probePin = 13;
int sensePin = A0;

unsigned long MAX_UNSIGNED_LONG = -1;


int cycleStart;
void setup() {
  // initialize Leds
  Serial.begin(500000);
  pinMode(onPin, INPUT);
  pinMode(lwPin, INPUT);
  pinMode(mwPin, INPUT);
  pinMode(kwPin, INPUT);
  pinMode(ukwPin, INPUT);
  
  analogReference(DEFAULT);
  
  pinMode(probePin, OUTPUT);

  cycleStart = micros();
}

int maxCycles = 120 * 2; // should be an odd number
int mode = 0;
int cycles = 0;
unsigned long sumSense = 0;

void loop() {
  // flip every loop
  mode = !mode;
  if (mode == 0) {
    digitalWrite(probePin, HIGH);
  } else {
    digitalWrite(probePin, LOW);
  }
  sumSense += analogRead(sensePin);
  cycles += 1;

  if (cycles >= maxCycles) {
    send(sumSense * 1.0 / cycles);
    sumSense = 0;
    cycles = 0;
  }
}

void send(float capVal) {
  onVal = digitalRead(onPin);
  lwVal = digitalRead(lwPin);
  mwVal = digitalRead(mwPin);
  kwVal = digitalRead(kwPin);
  ukwVal = digitalRead(ukwPin);
  int volRead = analogRead(volPin);
  volVal = float(volRead - volReadMin) / (volReadMax - volReadMin) * 0xFF;
  volVal = min(volVal, 0xFF);
  volVal = max(volVal, 0);
  
  int trebRead = analogRead(trebPin);
  trebVal = float(trebRead - trebReadMin) / (trebReadMax - trebReadMin) * 0xFF;
  trebVal = min(trebVal, 0xFF);
  trebVal = max(trebVal, 0);
  
  Serial.print("On: ");
  Serial.print(onVal);
  Serial.print("\t");
  Serial.print("LW: ");
  Serial.print(lwVal);
  Serial.print("\t");
  Serial.print("MW: ");
  Serial.print(mwVal);
  Serial.print("\t");
  Serial.print("KW: ");
  Serial.print(kwVal);
  Serial.print("\t");
  Serial.print("UKW: ");
  Serial.print(ukwVal);
  Serial.print("\t");
  Serial.print("Vol: ");
  Serial.print(volVal);
  Serial.print("\t");
  Serial.print("Tre: ");
  Serial.print(trebVal);
  Serial.print("\t");
  Serial.print("Cap: ");
  Serial.print(capVal);
  Serial.print("\n");
}
