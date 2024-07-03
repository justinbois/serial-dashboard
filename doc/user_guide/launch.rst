Launching a dashboard
=====================

A dashboard may be launched directly from the command line, using the ```bokeh serve`` command line utility, or from a Python session or Jupyter notebook.


From the command line
-------------------------------

The most common use case is to launch the dashboard from the command line using the ``serialdashboard`` command. Its usage (which can also be ascertained by executing ``serialdashboard --help`` on the command line) is as follows.


	Usage: 
	  serialdashboard [OPTIONS]

	Options:
	  --port INTEGER             port at localhost for serving dashboard (default
	                             5006)
	  --browser TEXT             browser to use for dashboard (defaults to OS
	                             default)
	  --baudrate INTEGER         baud rate of serial connection (default 115200)
	  --maxcols INTEGER          maximum number of columns of data coming off of
	                             the board (default 10)
	  --delimiter TEXT           delimiter of data coming off of the board
	                             (default comma)
	  --columnlabels TEXT        labels for columns using delimiter specified with
	                             --delimiter flag (default is none)
	  --timecolumn TEXT          column (zero-indexed) of incoming data that
	                             specifies time (default none)
	  --timeunits TEXT           units of incoming time data (default ms)
	  --rollover INTEGER         number of data points to be shown on a plot for
	                             each column (default 400)
	  --glyph TEXT               which glyphs to display in the plotter; either
	                             lines, dots, or both (default lines)
	  --inputtype TEXT           whether input is ascii or bytes (default ascii)
	  --fileprefix TEXT          prefix of output files
	  --daqdelay INTEGER         approximate delay in milliseconds for data
	                             acquisition from the board (default 20)
	  --streamdelay INTEGER      delay in milliseconds between updates of the
	                             plotter and monitor (default 90)
	  --portsearchdelay INTEGER  delay in milliseconds for checks of serial
	                             devices (default 1000)
	  --help                     Show this message and exit.

The ``--port`` and ``--browser`` flags determine at which port and in which browser the dashboard is to live. Once the dashboard is launched, these cannot be changed.

The ``--daqdelay``, ``--streamdelay`` and ``--portsearchdelay`` flags also cannot be changed once the dashboard is launched. The values controlled by all other flags can be adjusted from within the dashboard; the flags serve only to populate the initial settings. This can be convenient if the dashboard is being used for a project with known properties. For example, it is convenient to launch a dashboard controlling and Arduino board with the sample sketch (described :ref:`here <A sample device>`) using

.. code-block:: bash

    serialdashboard --columnlabels "time (ms),signal,sine wave" --maxcols 3 --timecolumn 0


From Python
---------------------

From an instance of Python or IPython, you can launch the serial dashboard with

.. code-block:: python

	import serial_dashboard
	serial_dashboard.launch()

The ``serial_dashboard.launch()`` function has the same keyword arguments as the flags for the command line interface, above (with the exception of ``help``). For example, to launch a dashboard with the sample sketch, one would use

.. code-block:: python
	
	serial_dashboard.launch(columnlabels="time (ms),signal,sine wave", maxcols=3, timecolumn=0)


From within a Jupyter notebook
---------------------------------

A dashboard may live within a Jupyter notebook. To enable this, use the ``serial_dashboard.app()`` function. (You will need to have `jupyter_bokeh <https://github.com/bokeh/jupyter_bokeh>`_ installed.)

.. code-block:: python

	import serial_dashboard
	import bokeh.io

	bokeh.io.output_notebook()

	dashboard_app = serial_dashboard.app()

	bokeh.io.show(dashboard_app)

If you want the same defaults as in the above example, use

.. code-block:: python

	serial_dashboard.app(columnlabels="time (ms),signal,sine wave", maxcols=3, timecolumn=0)


Using bokeh serve
---------------------------

Many users serve Bokeh-based apps using the ``bokeh serve`` command line tool. To launch a dashboard this way, you need to make a script per the specification of the ``bokeh serve`` tool. Such a script is as follows.

.. code-block:: python

	import bokeh.plotting
	import serial_dashboard

	app = serial_dashboard.app()

	app(bokeh.plotting.curdoc())

Then, to launch the app, save the script in a file (say, named ``launchscript.py``) and do the following on the command line.

.. code-block:: bash

    bokeh serve --show launchscript.py