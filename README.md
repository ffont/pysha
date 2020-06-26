# Pysha

**Pysha** is a Python 3 app to use Push2 as a standalone MIDI controller. Simply run `app.py` on a computer connected to Push2 and with a MIDI interface than can be used to output MIDI messages. Pysha can work on a Raspberry Pi so you can use Push2 as a standalone controller without your laptop around. The name is some sort of blend of the names of the technologies it involves. Generic instructions to run it:

```
pip install -r requirements.txt
python app.py
```

Pysha is based on [push2-python](https://github.com/ffont/push2-python). `push2-python` requires [pyusb](https://github.com/pyusb/pyusb) which is based in [libusb](https://libusb.info/). You'll most probably need to manually install `libusb` for your operative system if `pip install -r requirements.txt` does not do it for you. Moreover, to draw on Push2's screen, Pysha uses [`pycairo`](https://github.com/pygobject/pycairo) Python package. You'll most probably also need to install [`cairo`](https://www.cairographics.org/) if `pip install -r requirements.txt` does not do it for you (see [this page](https://pycairo.readthedocs.io/en/latest/getting_started.html) for info on that).


## Features

I designed Pysha (and I continue to update it) with the only purpose to serve my own specific needs. In my setup, I run Pysha on a Rapsberry Pi and connected to Push2. Push2 is used as my main source of MIDI input, and the generated MIDI is routed to a Squarp Pyramid sequencer. From there, Pyramid connects to all the other machines in the setup. These are the features that Pysha has currently implemented:

* Play melodies and chords in a chromatic scale mode
* Use classic 4x4 (and up to 8x8!) pad grid in the rhythm layout mode
* Choose between channel aftertouch and polyphonic aftertouch
* Use *accent* mode for fixed 127 velocity playing
* Interactively adjust aftertouch sensitivity curves
* Merge MIDI in from a MIDI input (using a MIDI intergace with the Rapsberry Pi) and also send it to the main MIDI out
* Interactively configure MIDI in/out settings
* Select Pyramid tracks and show track number information on screen
* Show track instrument information and sync colors (with preloaded information about what wach Pyramid track is routed to)
* Temporarily disable screen rendering for slow Raspberry Pi's (like mine!)
* Save current settings so these are automatically loaded on next run
* Raspberry Pi configuration instructions to load Pysha on startup!


## Instructions for have this running on a RaspberryPi

These are instructions to have the script running on a Rapsberry Pi and load at startup. I'm using this with a Raspberry Pi 2 and Raspbian 2020-02-13. It works a bit slow but it works. I also tested on a Raspberry Pi 4 and it is much faster and reliable.

1. Install system dependencies
```
sudo apt-get update && sudo apt-get install -y libusb-1.0-0-dev libcairo2-dev python3 python3-pip git libasound2-dev libatlas-base-dev
```

2. Clone the app repository
```
git clone https://github.com/ffont/pysha.git
```

3. Install Python dependencies
```
cd pysha
pip3 install -r requirements.txt
```

4. Configure permissions for using libusb without sudo (untested with these specific commands, but should work)

Create a file in `/etc/udev/rules.d/50-push2.rules`...

    sudo nano /etc/udev/rules.d/50-push2.rules

...with these contents:

    add file contents: SUBSYSTEM=="usb", ATTR{idVendor}=="2982", ATTR{idProduct}=="1967", GROUP="audio"

Then run:

    sudo udevadm control --reload-rules
    sudo udevadm trigger


5. Configure Python script to run at startup:

Create file in `/lib/systemd/system/pysha.service`...

    sudo nano /lib/systemd/system/pysha.service

...with these contents:

```
[Unit]
Description=Pysha
After=network-online.target

[Service]
WorkingDirectory=/home/pi/pysha
ExecStart=/usr/bin/python3 /home/pi/pysha/app.py                                                
StandardOutput=syslog
User=pi

[Install]
WantedBy=multi-user.target
```

Set permissions to file:

    sudo chmod 644 /lib/systemd/system/pysha.service


Enable the service (and do the linger thing which really I'm not sure if it is necessary nor what it does)

    loginctl enable-linger pi
    sudo systemctl enable pysha.service
    sudo systemctl status pysha.service

After that, the app should at startup. Logs got o `syslog` (check them running `tail -300f /var/log/syslog`)



