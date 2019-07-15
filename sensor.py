from datetime import timedelta, datetime
import logging
from struct import unpack

from bluepy import btle
from bluepy.btle import BTLEException
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_FORCE_UPDATE, CONF_MONITORED_CONDITIONS, CONF_NAME, CONF_MAC,
    DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_TEMPERATURE, DEVICE_CLASS_BATTERY
)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import voluptuous as vol


_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

DEFAULT_NAME = 'Inkbird'

# Sensor types are defined like: Name, units
SENSOR_TYPES = {
    'temperature': [DEVICE_CLASS_TEMPERATURE, 'Temperature', '°C'],
    'humidity': [DEVICE_CLASS_HUMIDITY, 'Humidity', '%'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Inkbird thermostat."""
    _LOGGER.info(">>> The inkbird component is ready!")

    dataIn = InkbirdDataRequest(config.get(CONF_MAC))
    devs = [] 

    for parameter in config[CONF_MONITORED_CONDITIONS]:
        name = SENSOR_TYPES[parameter][1]
        uom = SENSOR_TYPES[parameter][2]

        prefix = config.get(CONF_NAME)
        if prefix:
            name = "{} {}".format(prefix, name)

        devs.append(InkbirdSensor(dataIn, parameter, uom, name))

    add_entities(devs)


class InkbirdDataRequest(object):

    def __init__(self, mac):
        """Initialize the thermometer."""
        self.mac = mac
        self.temperature = None
        self.humidity = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the data from the thermometer."""
        try:
            dev = btle.Peripheral(self.mac)
            readings = dev.readCharacteristic(40)
        except BTLEException as error:
            _LOGGER.error("Error occurred while fetching data: %s", error)
            return False
        _LOGGER.debug("raw readings is %s", readings)
        temperature, humidity = unpack("<HH",readings[0:4])
        self.temperature = temperature/100
        self.humidity = humidity/100
        return True

class InkbirdSensor(Entity):
    """Representation of a Inkbird Sensor."""

    def __init__(self, dataIn, parameter, uom, name):
        """Initialize the sensor."""
        self.dataIn = dataIn
        self.data = []
        self._unit_of_measurement = uom
        self._name = name
        self.parameter = parameter
        self._current_temperature = None
        self._current_humidity = None
        self.update()
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the state of the sensor."""
        return self._current_temperature

    @property
    def current_humidity(self):
        """Return the state of the sensor."""
        return self._current_humidity

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    @property
    def should_poll(self):
        """Return the name of the sensor."""
        _LOGGER.debug("Should_Poll called")
        return True

    def update(self):
        """Get the latest data and use it to update our sensor state."""
        _LOGGER.debug("calling update .. ")
        update = self.dataIn.update()
        if update == True:
            self.data = getattr(self.dataIn,self.parameter)
            self._state = self.data
        return True
