# magicbandreader
Reads magic bands and plays sounds and lights up leds, just like the real thing.

# Install
*See youtube video TBD
*Install on Raspbian /home/pi
*sudo sh install.sh
*vi magicband.py. and edit the led counts for your build
*sudo vi /etc/rc.local
**Before the exit 0 line add:
** (cd /home/pi; sudo python3 magicband.py &)
*sudo reboot now
