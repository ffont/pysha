# Push2 Standalone Controller

Python 3 utility to use Push2 as a standalone MIDI controller. Simply run `app.py` on a computer connected to Push2 and with a MIDI interface than can be used to output MIDI messages. Instructions to run it (whout might want to create a virtualenvironment)):

```
pip install -r requirements.txt
python app.py
```

This utility is based on [push2-python](https://github.com/ffont/push2-python). `push2-python` which requires [pyusb](https://github.com/pyusb/pyusb) which is based in [libusb](https://libusb.info/). You'll most probably need to manually install `libusb` for your operative system if `pip install -r requirements.txt` does not do it for you. Moreover, to draw on Push2's screen, we use [`pycairo`](https://github.com/pygobject/pycairo) Python package. You'll most probably also need to install [`cairo`](https://www.cairographics.org/) if `pip install -r requirements.txt` does not do it for you (see [this page](https://pycairo.readthedocs.io/en/latest/getting_started.html) for info on that).

WARNING: current implementation is a quick hack. I should find some time to organise the code nicely, etc, etc.