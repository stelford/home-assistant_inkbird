import asyncio
from collections import OrderedDict
from datetime import timedelta, datetime
import logging
from random import randint
import re
from struct import unpack
import signal
import time

# from bluepy import btle
# from bluepy.btle import BTLEException, Scanner, DefaultDelegate
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_FORCE_UPDATE, CONF_MONITORED_CONDITIONS, CONF_NAME, CONF_MAC,
    DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_TEMPERATURE, DEVICE_CLASS_BATTERY
)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import voluptuous as vol


DOMAIN = 'Inkbird'
DEFAULT_NAME = 'Inkbird'
_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)
# Sensor types are defined like: Name, units
SENSOR_TYPES = {
    'updater': [None, 'Updater', None],
    'temperature': [DEVICE_CLASS_TEMPERATURE, 'Temperature', '°C'],
    'humidity': [DEVICE_CLASS_HUMIDITY, 'Humidity', '%'],
    'battery': [DEVICE_CLASS_BATTERY, 'Battery', '%'],
}

STATE_ATTR_TEMPERATURE = "temperature"
STATE_ATTR_HUMIDITY = "humidity"
STATE_ATTR_BATTERY = "battery"

ENTITY_ITEM = {
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required('devices'):
        vol.All(cv.ensure_list, [OrderedDict(ENTITY_ITEM)])
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Inkbird thermostat."""
    _LOGGER.info(">>> The inkbird component is ready!")

    inkbird_devices = []

    for device in config['devices']:
        for parameter in device['monitored_conditions']:
            name = SENSOR_TYPES[parameter][1]
            uom = SENSOR_TYPES[parameter][2]

            prefix = device['name']
            if prefix:
                name = "{} {}".format(prefix, name)
            entity_name = re.sub(' ', '_', name.lower())

            if parameter == "temperature":
                inkbird_devices.append( InkbirdThermalSensor(device['mac'], uom, name, entity_name) )
            elif parameter == "humidity":
                inkbird_devices.append( InkbirdHumiditySensor(device['mac'], uom, name, entity_name) )
            else:
                inkbird_devices.append( InkbirdBatterySensor(device['mac'], uom, name, entity_name) )

    inkbird_devices.append( InkbirdUpdater(hass, inkbird_devices) )
    add_entities(inkbird_devices, True)


class InkbirdUpdater(Entity):

    entity_id = "inkbird.updater"

    def __init__(self, hass, inkbird_devices):
        """Initialize the thermometer."""
        Entity.__init__(self)
        self._name = 'Inkbird Updater'
        self._state = None
        self._mac = None
        self.hass = hass
#        self.scanner = BleakScanner()
#        self.scanner.register
#        self.scanner.start()
        self.no_results_counter = 0
        self.inkbird_devices = inkbird_devices

    @property
    def mac(self):
        """Return the mac of the sensor."""
        return self._mac

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def should_poll(self):
        """Return the name of the sensor."""
        _LOGGER.debug("Should_Poll called")
        return False

    async def check_sensors(self):
        scanner = BleakScanner()
        scanner.register_detection_callback(self.handleDiscovery)

        await scanner.start()
        await asyncio.sleep(10.0)
        await scanner.stop()    
    
    async def async_added_to_hass(self):
        self.scanner = BleakScanner()
        self.scanner.register_detection_callback(self.handleDiscovery)
        await self.scanner.start()
    
    async def async_will_remove_from_hass(self):
        await self.scanner.stop(self)
	
    def update(self):
        """Get the latest data and use it to update our sensor state."""
        _LOGGER.debug("UPDATE called")
#        _LOGGER.debug(f"scanner here is {self.scanner}")
        return
        asyncio.run(self.check_sensors())
#        loop = asyncio.get_event_loop()
#        loop.run_until_complete(run())
        self._state = []
        return True

    def handleDiscovery(self, dev:BLEDevice, advdata:AdvertisementData):
        if (dev.name == "sps"):
            _LOGGER.debug(f"Discovered device {dev}")            
            temperature,others = advdata.manufacturer_data.popitem()
        
            temperature_bits = 16
            if temperature & (1 << (temperature_bits-1)):
                temperature -= 1 << temperature_bits
            temperature = "%2.2f" % (temperature / 100)
            humidity,junk,junk,battery = unpack("<hhbb",others[0:6])
            humidity = "%2.2f" % (humidity/100)
                                
            _LOGGER.debug(self.inkbird_devices)
            _LOGGER.debug(f" looking for {dev.address}")
            _LOGGER.debug(f" --> {temperature} - {humidity} - {battery} ")
            for device in self.inkbird_devices:
                # _LOGGER.debug(f" dev addr is {dev.address} and mac is {device.mac} with parameter of {device.parameter}")
                if dev.address == device.mac:
                    _LOGGER.debug(f" dev addr is {dev.address} and mac is {device.mac}")
                    old_state = self.hass.states.get(f"sensor.{device.entity_name}")
                    if old_state:
                        attrs = old_state.attributes
                    else:
                        attrs = None

                    if device.parameter == "temperature":
                        _LOGGER.debug(f" >>>> updating device {device.mac} with {temperature}")
                        device.temperature = temperature
                        device._state = temperature
                        #self.hass.states.set(f"sensor.{device.entity_name}", temperature, attrs)
                    elif device.parameter == "humidity":
                        _LOGGER.debug(f" >>>> updating device {device.mac} with {humidity}")
                        device.humidity = humidity
                        device._state = humidity
                        #self.hass.states.set(f"sensor.{device.entity_name}", humidity, attrs)
                    else:
                        _LOGGER.debug(f" >>>> updating device {device.mac} with {battery}")
                        device.battery = battery
                        device._state = battery
                        #self.hass.states.set(f"sensor.{device.entity_name}", battery, attrs)

                    self.async_schedule_update_ha_state()


class InkbirdThermalSensor(Entity):
    """Representation of a Inkbird Sensor."""

    def __init__(self, mac, uom, name, entity_name):
        """Initialize the sensor."""
        Entity.__init__(self)
        self._device_class = DEVICE_CLASS_TEMPERATURE
        self._mac = mac
        self._unit_of_measurement = uom
        self._name = name
        self._entity_name = entity_name
        self.parameter = "temperature"
        self._state = None
        self.temperature = None

    @property
    def mac(self):
        """Return the mac of the sensor."""
        return self._mac

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def entity_name(self):
        """Return the entity name of the sensor."""
        return self._entity_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit_of_measurement

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    @property
    def state_attributes(self):
        """Return the state attributes of the sun."""
        return {
            STATE_ATTR_TEMPERATURE: self.temperature
        }


class InkbirdHumiditySensor(Entity):
    """Representation of a Inkbird Sensor."""

    def __init__(self, mac, uom, name, entity_name):
        """Initialize the sensor."""
        Entity.__init__(self)
        self._device_class = DEVICE_CLASS_HUMIDITY
        self._mac = mac
        self._unit_of_measurement = uom
        self._name = name
        self._entity_name = entity_name
        self.parameter = "humidity"
        self._state = None
        self.humidity = None

    @property
    def mac(self):
        """Return the mac of the sensor."""
        return self._mac

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def entity_name(self):
        """Return the entity name of the sensor."""
        return self._entity_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit_of_measurement

    @property
    def state_attributes(self):
        """Return the state attributes of the sun."""
        return {
            STATE_ATTR_HUMIDITY: self.humidity
        }


class InkbirdBatterySensor(Entity):
    """Representation of a Inkbird Sensor."""

    def __init__(self, mac, uom, name, entity_name):
        """Initialize the sensor."""
        Entity.__init__(self)
        self._device_class = DEVICE_CLASS_BATTERY
        self._mac = mac
        self._unit_of_measurement = uom
        self._name = name
        self._entity_name = entity_name
        self.parameter = "battery"
        self._state = None
        self.battery = None

    @property
    def mac(self):
        """Return the mac of the sensor."""
        return self._mac

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def entity_name(self):
        """Return the entity name of the sensor."""
        return self._entity_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit_of_measurement

    @property
    def state_attributes(self):
        """Return the state attributes of the sun."""
        return {
            STATE_ATTR_BATTERY: self.battery
        }
