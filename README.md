# serial-dashboard

[![DOI](https://data.caltech.edu/badge/387582612.svg)](https://data.caltech.edu/badge/latestdoi/387582612)

This package provides a browser-based dashboard as a Python replacement for the serial plotter and serial monitor of the Arduino IDE. It includes extra utilities, such as plotting of a time axis (as opposed to strictly sample number), ability to save data transferred over serial, and ability to start and stop streams.

The documentation will soon be available [here](http://serial-dashboard.github.io/). For now, if you are feeling curious and/or brave, you can install it using

```bash
pip install serial-dashboard
```

on the command line. After it is installed, you can launch it from the command line using

```bash
serialdashboard
```

Note that it has not be thoroughly tested across platforms, but should at least work on macOS with Safari and Firefox. You should have installed recent versions of PySerial, NumPy, Pandas, and Bokeh and be running Python 3.7 or above.