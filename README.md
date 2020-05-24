# Push2 Standalone Controller

Python 3 utility to use Push2 as a standalone MIDI controller. Simply run `app.py` on a computer connected to Push2 and with a MIDI interface than can be used to output MIDI messages. Instructions to run it (whout might want to create a virtualenvironment)):

```
pip install -r requirements.txt
python app.py
```

This utility is based on [push2-python](https://github.com/ffont/push2-python). `push2-python` which requires [pyusb](https://github.com/pyusb/pyusb) which is based in [libusb](https://libusb.info/). You'll most probably need to manually install `libusb` for your operative system if `pip install -r requirements.txt` does not do it for you. Moreover, to draw on Push2's screen, we use [`pycairo`](https://github.com/pygobject/pycairo) Python package. You'll most probably also need to install [`cairo`](https://www.cairographics.org/) if `pip install -r requirements.txt` does not do it for you (see [this page](https://pycairo.readthedocs.io/en/latest/getting_started.html) for info on that).

WARNING: current implementation is a quick hack. I should find some time to organise the code nicely, etc, etc.


## Instructions for have this running on a RaspberryPi

These are instructions to have the script running on a RapsberryPi and load at startup. I'm using this with a RaspberryPi2 and Raspbian 2020-02-13. These instructions might not be accurate, but are hopefully useful. It worked for me!

1. Install system dependencies
```
sudo apt-get update && sudo apt-get install -y libusb-1.0-0-dev libcairo2-dev python3 python3-pip git libasound2-dev libatlas-base-dev
```

2. Clone the app repository
```
git clone https://github.com/ffont/push2-standalone-controller.git
```

3. Install Python dependencies
```
cd push2-standalone-controller
pip3 install -r requirements.txt
```

4. Configure permissions for using libusb without sudo (untested with these specific commands, but should work)

```
sudo echo SUBSYSTEM=="usb", ATTR{idVendor}=="2982", ATTR{idProduct}=="1967", GROUP="audio" > /etc/udev/rules.d/50-push2.rules 
sudo udevadm control --reload-rules
sudo udevadm trigger
```

5. Configure Python script to run at startup:

Create file in `/lib/systemd/system/push2_standalone_controller.service`...

    sudo nano /lib/systemd/system/push2_standalone_controller.service

...with these contents:

```
[Unit]
Description=Push2 Standalone Controller
After=network-online.target

[Service]
WorkingDirectory=/home/pi/push2-standalone-controller
ExecStart=/usr/bin/python3 /home/pi/push2-standalone-controller/app.py                                                
StandardOutput=syslog
User=pi

[Install]
WantedBy=multi-user.target
```

Set permissions to file:

    sudo chmod 644 /lib/systemd/system/push2_standalone_controller.service


Enable the service (and do the linger thing which really I'm not sure if it is necessary nor what it does)

    loginctl enable-linger pi
    sudo systemctl enable push2_standalone_controller.service
    sudo systemctl status push2_standalone_controller.service

After that, the app should at startup. Logs got o `syslog` (check them running `tail -300f /var/log/syslog`)



