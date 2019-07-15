This repo adds support for the Inkbird IBS-TH1 under Home Assistant.

Install this by dropping it into your config folder (path may vary
from install to install). In my install, this would be at
/config/custom_components/inkbird. 

Change your /config/configuration.yaml to have something like;

```
sensor:
  - platform: inkbird
    mac: '90:e2:02:9b:45:3a'
    name: 'Cians Room'
    monitored_conditions:
      - temperature
      - humidity
```

Obviously, the MAC and name you will change to tastes. The MAC you 
can find by using the scan.py inside helper_scripts. You can also
test in a 'once off' fashion by using the test_btle.py with the
changed MAC inside it.

There are a few caveats, of course;

1) I have not tested with multiple sensors yet
2) the sensor itself has a pretty nasty 'drop off' signal, at
   around 25 feet (in my experience). Bluetooth is not meant
   for long range
3) The code is based on the Xiaomi Sensor, and as such, it double
   polls if you have both temperature and humidity in there. The
   Inkbird mini really doesn't like getting "Spammed", so I put in
   a throttle for 60s. Reducing that will not help but, it's your
   choice to make.
