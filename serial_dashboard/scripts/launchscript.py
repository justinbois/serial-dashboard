# To launch the serial dashboard using this script, do
#
#  bokeh serve --show launchscript.py
#
# on the command line on the same line as this .py file.
#
# This is not commonly used, since you can launch the dashboard
# directly if the package is installed properly by entering
#
#   serialdashboard
#
# on the command line.

import bokeh.plotting

import serial_dashboard

# Build app
app = serial_dashboard.app()

# Build it with curdoc
app(bokeh.plotting.curdoc())
