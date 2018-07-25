import uinput
import time
from os import system
import RPi.GPIO as GPIO

batMax = 4.2
batMin = 3.75
batRange = batMax-batMin

graphStart = time.time()
def graphTime():
    return time.time()-graphStart

GPIO.setmode(GPIO.BCM)

trinketPin = 15

GPIO.setup(trinketPin, GPIO.OUT)
GPIO.output(trinketPin, True) #Notify Trinket that Pi is on



LEDs = [4, 5, 6, 7]

def setupLEDs():
    for pin in LEDs:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, False)

setupLEDs()

def clearGraph():
    for pin in LEDs:
        GPIO.output(pin, False)

def setGraph(num):
    clearGraph()
    frac = num-int(num)
    for i in range(min(len(LEDs), int(num))):
        if i == int(num)-1:
            blink = (time.time()*10)%10<5 and frac > 0.5
            GPIO.output(LEDs[i], blink)
            #print(blink)
        else:
            GPIO.output(LEDs[i], True)

def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)
 
        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low
 
        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
 
        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1
 
        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout
 
# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
 
# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)
 

system("modprobe uinput")

joyMaxVal = 1024
joyMidVal = int(joyMaxVal/2)

device = uinput.Device([
    uinput.BTN_THUMBL,
    uinput.BTN_THUMBR,
    uinput.ABS_X + (0, joyMaxVal, 0, 0),
    uinput.ABS_Y + (0, joyMaxVal, 0, 0),
    uinput.ABS_RX + (0, joyMaxVal, 0, 0),
    uinput.ABS_RY + (0, joyMaxVal, 0, 0),
    uinput.BTN_X,
    uinput.BTN_Y,
    uinput.BTN_Z,
    uinput.BTN_A,
    uinput.BTN_B,
    uinput.BTN_C,
    uinput.BTN_DPAD_UP,
    uinput.BTN_DPAD_DOWN,
    uinput.BTN_DPAD_LEFT,
    uinput.BTN_DPAD_RIGHT,
    uinput.BTN_SELECT,
    uinput.BTN_START,
])


class DigitalKey(object):
    def __init__(self, pin, key, val=0):
        self.pin = pin
        self.key = key
        self.val = 0
        GPIO.setup(self.pin, GPIO.IN)

    def run(self):
        curVal = GPIO.input(self.pin)
        if curVal != self.val:
            device.emit(self.key, curVal)
            self.val = curVal

class AnalogKey(object):
    def __init__(self, adc_pin, key, val=0, btn=False):
        self.adc_pin = adc_pin
        self.key = key
        self.val = val
        self.vals = [0]
        self.btn = btn
        self.time = 0
        self.emit = False
        self.press = "up"

    def run(self):

        if len(self.vals) > 6:
            self.vals = self.vals[1:]

        curVal = readadc(self.adc_pin, SPICLK, SPIMOSI, SPIMISO, SPICS)#/self.div

        self.vals.append(curVal)
        
        avg = 0

        for i in range(len(self.vals)):
            avg+=self.vals[i]/len(self.vals)

        avg = int(avg)

        avg = 0 if avg > 20 else 1

        curVal = int(curVal/20+0.5)*20

        if self.btn:
            if self.val != avg:
                device.emit(self.key, avg)
                
            self.val = avg
        else:
            if curVal != self.val:
                device.emit(self.key, curVal)
            self.val = curVal
        

mapPins = [
    DigitalKey(16, uinput.BTN_DPAD_UP),
    DigitalKey(17, uinput.BTN_DPAD_RIGHT),
    DigitalKey(18, uinput.BTN_DPAD_DOWN),
    DigitalKey(19, uinput.BTN_DPAD_LEFT),
    DigitalKey(20, uinput.BTN_A),
    DigitalKey(21, uinput.BTN_B),
    DigitalKey(22, uinput.BTN_X),
    DigitalKey(23, uinput.BTN_Y),
    DigitalKey(24, uinput.BTN_START),
    DigitalKey(25, uinput.BTN_SELECT),
    DigitalKey(26, uinput.BTN_Z),
    DigitalKey(27, uinput.BTN_C),
    AnalogKey(0, uinput.ABS_X),
    AnalogKey(1, uinput.ABS_Y),
    AnalogKey(2, uinput.BTN_THUMBL, btn=True),
    AnalogKey(5, uinput.ABS_RX),
    AnalogKey(4, uinput.ABS_RY),
    AnalogKey(3, uinput.BTN_THUMBR, btn=True),
]

graphNum = 1

try:
    while True:
        for i in range(len(mapPins)):
            mapPins[i].run()
        time.sleep(0.02)
        
        bat_frac = ((readadc(7, SPICLK, SPIMOSI, SPIMISO, SPICS)/1023)*5-batMin)/batRange
        setGraph(bat_frac*5)
finally:
    GPIO.cleanup()
