#!/usr/bin/env python3

from bluepy import btle
from struct import unpack


MAC='90:e2:02:9b:45:3a'


def scanDevices():
  pass

# feel free to use these to walk the inkbird device.. although I noticed 
# more than once that mine has a habit of 'going away' when hit heavily
# if you want to, uncomment the calls below
def iterateServices():
  print("Services...")
  for svc in dev.services:
      print( str(svc) )

def iterateCharacteristics():
  print("Characteristics...")
  for char in dev.getCharacteristics():
      print( char )
      print( char.__dict__ )
      print( char.uuid )
      if char.supportsRead():
        try:
          val = char.read()
          print(f"raw val is {val}")
          print("converted value is ", binascii.b2a_hex(val))
        except:
          print("ERROR - attribute can't be read probably")
      else:
        print("Skipping - attribute can't be read probably")

print("Connecting...")
dev = btle.Peripheral(MAC)
# iterateServices()
# iterateCharacteristics()


# Characteristic fff2 seems to be temperature and humidity -> 0000fff2-0000-1000-8000-00805f9b34fb 
# the fff2 has a read handle at 40 and (I am guessing here) a description handle at 39
readings = dev.readCharacteristic(40)
print(f"raw readings is {readings}")
temperature, humidity = unpack("<HH",readings[0:4])
print(f"temperature is {temperature/100}")
print(f"humidity is {humidity/100}")
