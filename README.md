This repo adds support for the Inkbird IBS-TH1 under Home Assistant.

![Example Output inside Home Assistant](room-temps.png)

Install this by dropping it into your config folder (path may vary
from install to install). In my install, this would be at
/config/custom_components/inkbird. 

Change your /config/configuration.yaml to have something like;
NOTE: MAC address should be lowercase

```
sensor:
  - platform: inkbird
    devices:
      - mac: '90:e2:02:9b:45:3a'
        name: 'Cians Room'
        monitored_conditions:
          - temperature
          - humidity
          - battery
      - mac: '90:e2:02:9b:4b:64'
        name: 'Kats Room'
        monitored_conditions:
          - temperature
          - humidity
          - battery
```

Obviously, the MAC and name you will change to your devices. The MAC you 
can find by using the scan.py inside helper_scripts. You can also
test in a 'once off' fashion by using the test_btle.py script with your
MAC updated inside it.

Every time a scan_interval is hit (previously set at 60s)
then the Inkbird.Updater will scan the btle for any broadcasts for 10s.
The Inkbird sends out a broadcast every 10s as well. This means that
from time to time, we won't get lucky and listen at the right time.

That said, there is no more btle connections happening (as it's using
broadcasted data from the devices only now). It's also vastly more
power efficient.
