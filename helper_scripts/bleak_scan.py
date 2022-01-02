import asyncio
from bleak import discover
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from struct import unpack
import time


def printInkbird(dev:BLEDevice,stuff):
#    print(dev)
    if (dev.name == "sps"):

        data = dev.metadata['manufacturer_data']
        temperature,others = data.popitem()
    

        temperature_bits = 16
        if temperature & (1 << (temperature_bits-1)):
            temperature -= 1 << temperature_bits
        temperature = "%2.2f" % (temperature / 100)
        humidity,junk,junk,battery = unpack("<hhbb",others[0:6])
        humidity = "%2.2f" % (humidity/100)
                            
        print(f" This is {dev.address}")
        print(f" --> Temp: {temperature} - Humidity: {humidity} - Battery: {battery} ")


async def doesnotwork():
    # does not work - Inkbird sends out two BLTE messages - once with "unknown" 
    #   as the name with no data, and a second with the name and data. Bleak will
    #   pick up on one or the other and sometimes not give data back
    devices = await discover()
    for d in devices:
        print(d)
        printInkbird(d)

async def run():
    scanner = BleakScanner()
    scanner.register_detection_callback(printInkbird)
    await scanner.start()
    await asyncio.sleep(5.0)
    await scanner.stop()


while(1):
	loop = asyncio.get_event_loop()
	loop.run_until_complete(run())
	time.sleep(1)
