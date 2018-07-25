
int waitKillTime = 20; //how long to wait after Raspberry Pi has powered off to shut off battery (in seconds)

int enablePin = 2; //Pin connected to PowerBoost EN (enable) pin
int signalPin = 0; //Pin connected to Raspberry Pi (If HIGH, Raspberry Pi is ON, if LOW, Raspberry Pi is OFF)

void setup() {
  // put your setup code here, to run once:
  pinMode(enablePin, OUTPUT); //Controls the PowerBoost EN (enable) pin
  pinMode(signalPin, INPUT); //Reads Raspberry Pi state (on/off)
  digitalWrite(enablePin, HIGH); //Keep the PowerBoost on
  while(digitalRead(signalPin)==LOW){ //wait for pin to go HIGH, signaling that Raspberry Pi is on.
    delay(100);
  }
}

void loop(){
  if(digitalRead(signalPin)==LOW){ //if pin is LOW, Raspberry Pi has powered off or is rebooting.
    delay(1000*waitKillTime);
    if(digitalRead(signalPin)==LOW){ //Another check to make sure Pi is actually powered off (not rebooting or pin went low for some reason)
      digitalWrite(enablePin, LOW);
    }
  }
}
