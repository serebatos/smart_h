__author__ = 'Serebatos'
import RPi.GPIO as GPIO
import time, sys

# power manage functions
def switch(pin, val):
        GPIO.output(pin,val)
        return

def turn_on(pin):
        switch(pin, GPIO.HIGH)
        return

def turn_off(pin):
        switch(pin,GPIO.LOW)
        return

# to use Raspberry Pi board pin numbers

if len(sys.argv)>2:
        cmd=sys.argv[2]
        pin=int(sys.argv[1])
else:
        cmd='0'
        pin=26

print 'Command is:', cmd
GPIO.setmode(GPIO.BOARD)
# set up GPIO output channel
GPIO.setup(pin, GPIO.OUT)

if cmd=='0':
        print 'Turning off'
        turn_off(pin)
        GPIO.cleanup(pin)
elif cmd=='1':
        print 'Turning on'
        turn_on(pin)
