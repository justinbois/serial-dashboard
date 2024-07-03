import asyncio
import sys

import numpy as np
import pandas as pd

import serial
import serial.tools.list_ports

import bokeh.plotting
import bokeh.io
import bokeh.layouts
import bokeh.driving

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler

from . import boards
from . import callbacks
from . import comms
from . import parsers

# Allowed values of selector parameters
allowed_baudrates = (
    300,
    1200,
    2400,
    4800,
    9600,
    19200,
    38400,
    57600,
    74880,
    115200,
    230400,
    250000,
    500000,
    1000000,
    2000000,
)

allowed_time_columns = ("none", 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

allowed_delimiters = (
    "comma",
    "space",
    "tab",
    "whitespace",
    "vertical line",
    "semicolon",
    "asterisk",
    "slash",
)

allowed_timeunits = ("none", "µs", "ms", "s", "min", "hr")

allowed_glyphs = ("lines", "dots", "both")

allowed_rollover = (100, 200, 400, 800, 1600, 3200)

max_max_cols = 10


def _check_baudrate(baudrate):
    if baudrate not in allowed_baudrates:
        err_str = "Inputted baudrate {baudrate} is not allowed. Allowed baudrates (in units of baud = bits per second) are: \n"

        for br in allowed_baudrates:
            err_str += f"  {br}\n"

        raise RuntimeError(err_str)


def _check_maxcols(maxcols):
    if maxcols < 1 or maxcols > max_max_cols:
        raise RuntimeError(
            f"Inputted maxcols {maxcols} is invalid. maxcols must be between 1 and {max_max_cols}."
        )


def _check_delimiter(delimiter):
    if delimiter not in allowed_delimiters:
        err_str = f'Inputted delimiter "{delimiter}" is not allowed. Allowed delimiters are: \n'

        for dl in allowed_delimiters:
            err_str += f"  {dl}\n"

        raise RuntimeError(err_str)


def _check_timecolumn(timecolumn, maxcols):
    if timecolumn == "none":
        return None

    try:
        timecolumn = int(timecolumn)
    except:
        raise RuntimeError(
            "Inputted timecolumn {timecolumn} is invalid. timecolumn must be an integer."
        )

    if timecolumn < 0 or timecolumn >= maxcols:
        raise RuntimeError(
            f"Inputted timecolumn {timecolumn} is invalid. Must have 0 ≤ timecolumn < maxcols. You have selected maxcols = {maxcols}."
        )


def _check_timeunits(timeunits):
    if timeunits not in allowed_timeunits:
        err_str = f'Inputted timeunits "{timeunits}" is not allowed. Allowed time units are: \n'

        for tu in allowed_timeunits:
            err_str += f"  {tu}\n"

        raise RuntimeError(err_str)


def _check_rollover(rollover):
    if rollover not in allowed_rollover:
        err_str = f'Inputted rollover "{rollover}" is not allowed. Allowed rollover values are: \n'

        for ro in allowed_rollover:
            err_str += f"  {ro}\n"

        raise RuntimeError(err_str)


def _check_inputtype(inputtype):
    if inputtype not in ["ascii", "bytes"]:
        raise RuntimeError(
            'Inputted input type "{inputtype}" is not allowed. Must be either "ascii" or "bytes".'
        )


def _check_glyph(glyph):
    if glyph not in allowed_glyphs:
        err_str = (
            f'  Inputted glyph "{glyph}" is not allowed. Allowed glyph choises are: \n'
        )

        for g in allowed_glyphs:
            err_str += f"  {g}\n"

        raise RuntimeError(err_str)


class SerialConnection(object):
    """Class containing details about a serial connection.

    Attributes
    ----------
    ser : serial.Serial instance
        Serial connection to a device.
    port : str
        Name of the port of the connection. This is not the device name,
        but a descriptive name.
    baudrate : int
        Baud rate of the connection
    bytesize : int
        Number of data bits. Possible values: serial.FIVEBITS,
        serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS
    parity : int
        Enable parity checking. Possible values: serial.PARITY_NONE,
        serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK,
        serial.PARITY_SPACE.
    stopbits : int
        Number of stop bits. Possible values: serial.STOPBITS_ONE,
        serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO
    ports : list
        List of ports that are available. Each entry is a
        serial.tools.list_ports_common.ListPortInfo instance.
    available_ports : dict
        A dictionary with the descriptive port names as keys and strings
        with the name of the ports such that they can be opened with
        `serial.Serial()` as values.
    reverse_available_ports : dict
        A dictionary with the descriptive port names as values and
        strings with the name of the ports such that they can be opened
        with `serial.Serial()` as keys.
    port_status : str
        The status of the port. Either "disconnected", "establishing",
        "connected", or "failed".
    daq_task : async task
        Task for data acquisition.
    daq_delay : float
        Approximate time, in milliseconds, between data acquisitions.
    port_search_task : async task
        Task for checking for available ports.
    port_search_delay : float
        Approximate time, in milliseconds, between checks of available
        ports.
    kill_app : bool
        If True, kill the connect/app.
    """

    def __init__(
        self,
        port=None,
        baudrate=115200,
        daq_delay=20,
        port_search_delay=1000,
        bytesize=8,
        parity="N",
        stopbits=1,
    ):
        """Create an instance storing information about a serial
        connection.

        Parameters
        ----------
        port : str, default None
            If given, name of the port to connect to. If None, no device
            is connected.
        baudrate : int
            Baud rate of the connection
        daq_delay : float
            Approximate time, in milliseconds, between data acquisitions.
        bytesize : int
            Number of data bits. Possible values: serial.FIVEBITS,
            serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS
        parity : int
            Enable parity checking. Possible values: serial.PARITY_NONE,
            serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK,
            serial.PARITY_SPACE.
        stopbits : int
            Number of stop bits. Possible values: serial.STOPBITS_ONE,
            serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO
        """
        self.ser = None
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.ports = []
        self.available_ports = dict()
        self.reverse_available_ports = dict()
        self.port_status = "disconnected"
        self.daq_task = None
        self.daq_delay = daq_delay
        self.port_search_task = None
        self.port_search_delay = port_search_delay
        self.kill_app = False

        # Attempt to connect to a port if provided
        if port is None:
            self.port = port
        else:
            self.connect(port)

    def portsearch(self, on_change=True):
        """Search for ports and update port information.

        Parameters
        ----------
        on_change : bool, default True
            If True, only update `ports`, `available_ports`, and
            `reverse_available_ports` attributes if there was a change
            in the available ports.
        """
        ports = serial.tools.list_ports.comports()

        if not on_change or ports != self.ports:
            self.ports = [port for port in ports]

            options = [comms.device_name(port_name) for port_name in ports]

            # Dictionary of port names and name in port selector
            self.available_ports = {
                port_name.device: option_name
                for port_name, option_name in zip(ports, options)
            }

            # Reverse lookup for value in port selector to port name
            self.reverse_available_ports = {
                option_name: port_name.device
                for port_name, option_name in zip(ports, options)
            }

    def connect(self, port, allow_disconnect=False, handshake=True):
        """Connect to a port.

        Parameters
        ----------
        port : str, int, or serial.tools.list_ports_common.ListPortInfo instance
            Port to which to connect. If an int, connect to port given
            by self.ports[port].
        allow_disconnect : bool, default True
            If already connected to a port, allow disconnection. If
            False, raise an exception if already connected.
        handshake : bool, default True
            If True, "handshake" with the connected device by closing,
            reopening connection waiting a second, and then clearing
            the input buffer.
        """
        # Disconnect, if necessary
        if self.ser is not None and self.ser.is_open:
            if allow_disconnect:
                try:
                    self.ser.close()
                    self.ser = None
                except:
                    pass

                self.port_status = "disconnected"
            elif raise_exceptions:
                raise RuntimeError(f"Already connected to port {self.port}.")

        # Match requested port with known port
        if port in self.ports:
            port = port.device
        elif type(port) == int and port < len(self.ports):
            port = self.ports[port].device
        elif port in self.reverse_available_ports:
            port = self.reverse_available_ports[port]
        elif port not in self.available_ports:
            # A port search hasn't been done that includes port being asked for
            self.portsearch()

        # Indentify the port we're trying to connect to
        self.port = port

        # Make the connection
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
            )
            self.port_status = "connected"
        except:
            self.ser = None
            self.port_status = "failed"

            raise RuntimeError(f"Connection to port {port} failed.")

        # Handshake
        if handshake:
            comms.handshake_board(self.ser)

    def disconnect(self):
        """Disconnect port."""
        try:
            self.ser.close()
        except:
            pass

        self.ser = None
        self.port_status = "disconnected"


class Controls(object):
    def __init__(
        self,
        baudrate=115200,
        max_cols=max_max_cols,
        delimiter="comma",
        columnlabels="",
        timecolumn="none",
        timeunits="ms",
        rollover=400,
        glyph="lines",
        inputtype="ascii",
        fileprefix="_tmp",
    ):
        """Create all of the controls for the serial dashboard."""
        self.plot_stream = bokeh.models.Toggle(
            label="stream", button_type="success", width=100
        )

        self.plot_clear = bokeh.models.Button(
            label="clear", button_type="warning", width=100
        )

        self.monitor_stream = bokeh.models.Toggle(
            label="stream", button_type="success", width=100
        )

        self.monitor_clear = bokeh.models.Button(
            label="clear", button_type="warning", width=100
        )

        self.plot_save = bokeh.models.Button(
            label="save", button_type="primary", width=100
        )

        self.plot_file_input = bokeh.models.TextAreaInput(
            title="file name", value=f"{fileprefix}.csv", width=150, visible=False
        )

        self.plot_write = bokeh.models.Button(
            label="save", button_type="primary", width=50, visible=False
        )

        self.plot_save_notice = bokeh.models.Div(
            text='<p style="font-size: 8pt;">No data saved.</p>', width=100
        )

        self.glyph = bokeh.models.RadioGroup(
            labels=list(allowed_glyphs), active=allowed_glyphs.index(glyph), width=50
        )

        self.monitor_save = bokeh.models.Button(
            label="save", button_type="primary", width=100
        )

        self.monitor_file_input = bokeh.models.TextAreaInput(
            title="file name", value=f"{fileprefix}.txt", width=150, visible=False
        )

        self.monitor_write = bokeh.models.Button(
            label="save", button_type="primary", width=50, visible=False
        )

        self.monitor_save_notice = bokeh.models.Div(
            text='<p style="font-size: 8pt;">No data saved.</p>', width=100
        )

        self.delimiter = bokeh.models.Select(
            title="delimiter",
            value=delimiter,
            options=list(allowed_delimiters),
            width=100,
        )

        self.rollover = bokeh.models.Select(
            title="plot rollover",
            value=str(rollover),
            options=[str(ro) for ro in allowed_rollover],
            width=100,
        )

        self.max_cols = bokeh.models.Spinner(
            title="maximum number of columns",
            value=max_cols,
            low=1,
            high=max_max_cols,
            step=1,
            width=100,
        )

        self.col_labels = bokeh.models.TextInput(
            title="column labels", value=columnlabels, width=200
        )

        # Set up port selector
        self.port = bokeh.models.Select(title="port", options=[], value="", width=200)

        # Set up baud rate with Arduino defaults
        self.baudrate = bokeh.models.Select(
            title="baud rate",
            options=[str(br) for br in allowed_baudrates],
            value=str(baudrate),
            width=100,
        )

        self.port_connect = bokeh.models.Button(
            label="connect", button_type="success", width=100
        )

        self.port_disconnect = bokeh.models.Button(
            label="disconnect", button_type="danger", width=100, disabled=True
        )

        self.port_status = bokeh.models.Div(
            text="<p><b>port status:</b> disconnected</p>", width=200
        )

        self.time_column = bokeh.models.Select(
            title="time column",
            value=timecolumn,
            options=[str(tc) for tc in allowed_time_columns],
            width=100,
        )

        self.time_units = bokeh.models.Select(
            title="time units",
            value=timeunits,
            options=list(allowed_timeunits),
            width=100,
        )

        self.input_window = bokeh.models.TextAreaInput(
            title="input", value="", width=150
        )

        self.input_send = bokeh.models.Button(
            label="send", button_type="primary", width=50, disabled=True
        )

        self.ascii_bytes = bokeh.models.RadioGroup(
            labels=["ascii", "bytes"], active=(0 if inputtype == "ascii" else 1)
        )

        self.shutdown = bokeh.models.Button(
            label="shut down dashboard", button_type="danger", width=310
        )

        self.confirm_shutdown = bokeh.models.Button(
            label="confirm shutdown",
            button_type="danger",
            width=150,
            visible=False,
            disabled=True,
        )

        self.cancel_shutdown = bokeh.models.Button(
            label="cancel shutdown",
            button_type="primary",
            width=150,
            visible=False,
            disabled=True,
        )


class SerialPlotter(object):
    def __init__(
        self,
        max_cols=max_max_cols,
        delimiter="comma",
        columnlabels="",
        timecolumn="none",
        timeunits="ms",
        rollover=400,
        glyph="lines",
    ):
        """Create a serial plotter."""
        self.prev_data_length = 0
        self.data = []
        self.time_column = "none" if timecolumn == "none" else int(timecolumn)
        self.time_units = timeunits
        self.max_cols = max_cols
        self.streaming = False
        self.sources = []
        self.delimiter = parsers._delimiter_convert(delimiter)
        self.col_labels = parsers._column_labels_str_to_list(
            columnlabels, self.delimiter, self.max_cols
        )
        self.lines = None
        self.dots = None
        self.lines_visible = glyph in ("lines", "both")
        self.dots_visible = glyph in ("dots", "both")
        self.rollover = rollover
        self.plot, self.legend, self.phantom_source = self.base_plot()

    def base_plot(self):
        """Build a plot of voltage vs time data"""
        # Set up plot area
        p = bokeh.plotting.figure(
            frame_width=600,
            frame_height=175,
            x_axis_label=parsers._xaxis_label(self.time_column, self.time_units),
            y_axis_label=" ",
            toolbar_location="above",
            title="serial plotter",
        )

        # No range padding on x: signal spans whole plot
        p.x_range.range_padding = 0

        # We'll sue whitesmoke backgrounds
        p.border_fill_color = "whitesmoke"

        # Put a phantom circle so axis labels show before data arrive
        phantom_source = bokeh.models.ColumnDataSource(
            data=dict(phantom_t=[0], phantom_y=[0])
        )
        p.scatter(source=phantom_source, x="phantom_t", y="phantom_y", visible=False)

        # Make an empty legend
        legend = bokeh.models.Legend(
            items=[],
            location="center",
            label_text_font_size="8pt",
            spacing=1,
            label_height=15,
            glyph_height=15,
            click_policy="hide",
        )

        p.add_layout(legend, "right")

        return p, legend, phantom_source


class SerialMonitor(object):
    def __init__(self, scroll_snap=True):
        """Create a serial monitor.

        Parameters
        ----------
        scroll_snap : bool, default True
            If True, use CSS scroll-snap in serial monitor. This should
            only be set to False for an old browser that does not have
            CSS scroll-snap.
        """
        # Use CSS scroll-snap to enable scrolling with default at bottom
        self.base_text = """<style>
.monitorHeader {
    background-color: whitesmoke;
    height: 20px;
    width: 630px;
}

.monitorData {
    border-style: solid;
    border-width: 10px;
    border-color: whitesmoke;
    background-color: white;
    width: 630px;
    height: 200px;
    overflow-y: scroll;
    overscroll-behavior-y: contain;
    scroll-snap-type: y proximity;
}

.monitorData > div:last-child {
  scroll-snap-align: end;
}

.monitorTitle {
    margin-left: 50px;
    margin-bottom: 0px;
}
</style>

<div class="monitorHeader">
  <p class="monitorTitle">
    <b>serial monitor</b>
  </p>
</div>

<div class="monitorData"><div><pre></pre></div></div>"""

        # As an alternative, can use text below. This is a hacky way to do
        # it with some rotations. The scroll bar will be on the left, and
        # mouse scroll wheel directions will be reversed from their usual.
        # This method may be useful for older browsers that do not have
        # CSS scroll-snap.
        self.alternative_base_text = """<style>
.monitorHeader {
    background-color: whitesmoke;
    height: 20px;
    width: 630px;
}

.monitorData {
    border-style: solid;
    border-width: 10px;
    border-color: whitesmoke;
    background-color: white;
    width: 630px;
    height: 200px;
    overflow: auto;
    transform: rotate(180deg);
}

.monitorInner {
    overflow: hidden;
    transform: rotate(180deg);
}

.monitorTitle {
    margin-left: 50px;
    margin-bottom: 0px;
}
</style>

<div class="monitorHeader">
  <p class="monitorTitle">
    <b>serial monitor</b>
  </p>
</div>

<div class="monitorData"><div class="monitorInner"><pre></pre></div></div>"""

        self.monitor = bokeh.models.Div(
            text=self.base_text if scroll_snap else self.alternative_base_text,
            background="whitesmoke",
            height=250,
            width=650,
            sizing_mode="fixed",
        )
        self.prev_data_length = 0
        self.data = []
        self.streaming = False


def _layout(plotter, monitor, controls):
    """Build layout of serial dashboard.

    Parameters
    ----------
    plotter : serial_dashboard.SerialPlotter instance
        Instance of plot and related data structures.
    monitor : serial_dashboard.SerialMonitor instance
        Instance of monitor and related data structures.
    controls : serial_dashboard.Controls instance
        Instance of widget controls.

    Returns
    -------
    output : bokeh.models.layouts.Row instance
        Layout of the dashboard.
    """
    plotter_buttons = bokeh.layouts.column(
        bokeh.models.Spacer(height=20),
        controls.plot_stream,
        bokeh.models.Spacer(height=20),
        controls.plot_clear,
        bokeh.models.Spacer(height=20),
        controls.plot_save,
        bokeh.layouts.row(
            controls.plot_file_input,
            bokeh.layouts.column(bokeh.models.Spacer(height=20), controls.plot_write),
        ),
        controls.plot_save_notice,
    )
    plotter_layout = bokeh.layouts.row(
        plotter_buttons,
        plotter.plot,
        bokeh.layouts.column(bokeh.models.Spacer(height=85), controls.glyph),
        margin=(30, 0, 0, 0),
        background="whitesmoke",
    )

    input_layout = bokeh.layouts.row(
        bokeh.models.Spacer(width=10),
        controls.input_window,
        bokeh.models.Spacer(width=20),
        bokeh.layouts.column(bokeh.models.Spacer(height=20), controls.input_send),
        bokeh.models.Spacer(width=20),
        bokeh.layouts.column(bokeh.models.Spacer(height=17), controls.ascii_bytes),
        background="whitesmoke",
        width=350,
    )

    shutdown_layout = bokeh.layouts.row(
        bokeh.layouts.column(bokeh.models.Spacer(height=10), controls.shutdown),
        bokeh.layouts.column(bokeh.models.Spacer(height=10), controls.cancel_shutdown),
        bokeh.layouts.column(bokeh.models.Spacer(height=10), controls.confirm_shutdown),
    )

    port_controls = bokeh.layouts.column(
        controls.port,
        controls.baudrate,
        bokeh.models.Spacer(height=10),
        controls.port_connect,
        controls.port_disconnect,
        controls.port_status,
        background="whitesmoke",
    )

    specs = bokeh.layouts.column(
        controls.max_cols,
        bokeh.models.Spacer(height=10),
        controls.delimiter,
        bokeh.models.Spacer(height=10),
        controls.col_labels,
        bokeh.models.Spacer(height=10),
        controls.time_column,
        bokeh.models.Spacer(height=10),
        controls.time_units,
        bokeh.models.Spacer(height=10),
        controls.rollover,
        background="whitesmoke",
    )

    monitor_buttons = bokeh.layouts.column(
        bokeh.models.Spacer(height=20),
        controls.monitor_stream,
        bokeh.models.Spacer(height=20),
        controls.monitor_clear,
        bokeh.models.Spacer(height=20),
        controls.monitor_save,
        bokeh.layouts.row(
            controls.monitor_file_input,
            bokeh.layouts.column(
                bokeh.models.Spacer(height=20), controls.monitor_write
            ),
        ),
        controls.monitor_save_notice,
    )

    monitor_layout = bokeh.layouts.row(
        monitor_buttons,
        bokeh.models.Spacer(width=15),
        monitor.monitor,
        bokeh.models.Spacer(width=10),
        margin=(30, 0, 30, 0),
        background="whitesmoke",
    )

    return bokeh.layouts.row(
        bokeh.layouts.column(port_controls, bokeh.models.Spacer(height=30), specs),
        bokeh.models.Spacer(width=20),
        bokeh.layouts.column(
            bokeh.layouts.row(
                input_layout, bokeh.models.Spacer(width=100), shutdown_layout,
            ),
            plotter_layout,
            monitor_layout,
        ),
    )


def app(
    baudrate=115200,
    maxcols=10,
    delimiter="comma",
    columnlabels="",
    timecolumn=None,
    timeunits="ms",
    rollover=400,
    glyph="lines",
    inputtype="ascii",
    fileprefix="_tmp",
    daqdelay=20,
    streamdelay=90,
    portsearchdelay=1000,
):
    """Returns a function that can be used as a Bokeh app.

    The app can be launched using `bokeh serve --show launchscript.py`,
    from the command line where the contents of `launchscript.py` are:

    .. code-block:: python

        import bokeh.plotting
        import serial_dashboard

        app = serial_dashboard.app()

        app(bokeh.plotting.curdoc())

    To launch the app programmatically with Python, do the following:

    This function should only be used if you need to programmatically
    access the app builder, for example for using the dashboard within
    a Jupyter notebook. To launch a dashboard in its own browser window,
    use `launch()` instead.

    Alternatively, if you want to launch in its own browser window
    programmatically, you can do the following.

    .. code-block:: python

        from bokeh.server.server import Server
        from bokeh.application import Application
        from bokeh.application.handlers.function import FunctionHandler
        import serial_dashboard

        app = serial_dashboard.app()

        app_dict = {'/serial-dashboard': Application(FunctionHandler(app))}
        server = Server(app_dict, port=5006)
        server.show('/serial-dashboard')
        server.run_until_shutdown()

    Parameters
    ----------
    port : int, default 5006
        Port at localhost for serving dashboard.
    browser : str, default None
        Browser to use for dashboard. If None, uses OS default.
    baudrate : int, default 115200
        Baud rate of serial connection. Allowed values are 300, 1200,
        2400, 4800, 9600, 19200, 38400, 57600, 74880, 115200, 230400,
        250000, 500000, 1000000, 2000000.
    maxcols : int, default 10
        Maximum number of columns of data coming off of the board.
    delimiter : str, default "comma"
        Delimiter of data coming off of the board. Allowed values are
        "comma", "space", "tab", "whitespace", "vertical line",
        "semicolon", "asterisk", "slash"
    columnlabels : str, default ""
        Labels for columnbs using the delimiter specified with
        `delimiter` keyword argument.
    timecolumn : int, default None
        Column (zero-indexed) of incoming data that specifies time
    timeunits : str, default "ms"
        Units of incoming time data. Allowed values are "none", "µs",
        "ms", "s", "min", "hr".
    rollover : int, default 400
        Number of data points to be shown on a plot for each column.
        Allowed values are 100, 200, 400, 800, 1600, 3200.
    glyph : str, default "lines"
        Which glyphs to display in the plotter. Allowed values are
        "lines", "dots", "both".
    inputtype : str, default "ascii"
        Whether input sent to the board is ASCII or bytes. Allowed
        values are "ascii", "bytes".
    fileprefix : str, default "_tmp"
        Prefix for output files
    daqdelay : float, default 20.0
        Roughly the delay in data acquisition from the board in
        milliseconds. The true delay is a bit above 80% of this value.
    streamdelay : int, default 90
        Delay between updates of the plotter and monitor in
        milliseconds.
    portsearchdelay : int, default 1000
        Delay between checks of connected serial devices in
        milliseconds.
    """
    # Time column is expected to be a string or an integer
    if timecolumn is None:
        timecolumn = "none"

    # We can be a bit flexible on delimiters
    delimiter_conversion = {
        ",": "comma",
        " ": "space",
        "\t": "tab",
        "\s": "whitespace",
        "|": "vertical line",
        ";": "semicolon",
        "*": "asterisk",
        "/": "slash",
    }
    if delimiter in delimiter_conversion:
        delimiter = delimiter_conversion[delimiter]

    # Check inputs
    _check_baudrate(baudrate),
    _check_maxcols(maxcols),
    _check_delimiter(delimiter),
    _check_timecolumn(timecolumn, maxcols),
    _check_timeunits(timeunits),
    _check_rollover(rollover),
    _check_glyph(glyph),
    _check_inputtype(inputtype),

    def _app(doc):
        # "Global" variables
        serial_connection = SerialConnection(
            baudrate=baudrate, daq_delay=daqdelay, port_search_delay=portsearchdelay
        )
        controls = Controls(
            baudrate=baudrate,
            max_cols=maxcols,
            delimiter=delimiter,
            columnlabels=columnlabels,
            timecolumn=timecolumn,
            timeunits=timeunits,
            rollover=rollover,
            glyph=glyph,
            inputtype=inputtype,
            fileprefix=fileprefix,
        )
        plotter = SerialPlotter(
            max_cols=maxcols,
            delimiter=delimiter,
            columnlabels=columnlabels,
            timecolumn=timecolumn,
            timeunits=timeunits,
            rollover=rollover,
            glyph=glyph,
        )
        monitor = SerialMonitor()

        app_layout = _layout(plotter, monitor, controls)

        # Start port sniffer
        serial_connection.port_search_task = asyncio.create_task(
            comms.port_search(serial_connection)
        )

        # Define and link on_click callbacks
        def _port_connect_callback(event=None):
            callbacks.port_connect_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.port_connect.on_click(_port_connect_callback)

        def _port_disconnect_callback(event=None):
            callbacks.port_disconnect_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.port_disconnect.on_click(_port_disconnect_callback)

        def _input_send_callback(event=None):
            callbacks.input_send_callback(plotter, monitor, controls, serial_connection)

        controls.input_send.on_click(_input_send_callback)

        def _monitor_stream_callback(event=None):
            callbacks.monitor_stream_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.monitor_stream.on_click(_monitor_stream_callback)

        def _monitor_clear_callback(event=None):
            callbacks.monitor_clear_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.monitor_clear.on_click(_monitor_clear_callback)

        def _monitor_save_callback(event=None):
            callbacks.monitor_save_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.monitor_save.on_click(_monitor_save_callback)

        def _monitor_write_callback(event=None):
            callbacks.monitor_write_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.monitor_write.on_click(_monitor_write_callback)

        def _plot_stream_callback(event=None):
            callbacks.plot_stream_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.plot_stream.on_click(_plot_stream_callback)

        def _plot_clear_callback(event=None):
            callbacks.plot_clear_callback(plotter, monitor, controls, serial_connection)

        controls.plot_clear.on_click(_plot_clear_callback)

        def _plot_save_callback(event=None):
            callbacks.plot_save_callback(plotter, monitor, controls, serial_connection)

        controls.plot_save.on_click(_plot_save_callback)

        def _plot_write_callback(event=None):
            callbacks.plot_write_callback(plotter, monitor, controls, serial_connection)

        controls.plot_write.on_click(_plot_write_callback)

        def _shutdown_callback(event=None):
            callbacks.shutdown_callback(plotter, monitor, controls, serial_connection)

        controls.shutdown.on_click(_shutdown_callback)

        def _cancel_shutdown_callback(event=None):
            callbacks.cancel_shutdown_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.cancel_shutdown.on_click(_cancel_shutdown_callback)

        def _confirm_shutdown_callback(event=None):
            callbacks.confirm_shutdown_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.confirm_shutdown.on_click(_confirm_shutdown_callback)

        # Define and link on_change callbacks
        def _port_select_callback(attr, old, new):
            callbacks.port_select_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.port.on_change("value", _port_select_callback)

        def _baudrate_callback(attr, old, new):
            callbacks.baudrate_callback(plotter, monitor, controls, serial_connection)

        controls.baudrate.on_change("value", _baudrate_callback)

        def _delimiter_select_callback(attr, old, new):
            callbacks.delimiter_select_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.delimiter.on_change("value", _delimiter_select_callback)

        def _time_column_callback(attr, old, new):
            callbacks.time_column_callback(
                plotter, monitor, controls, serial_connection
            )

        controls.time_column.on_change("value", _time_column_callback)

        def _time_units_callback(attr, old, new):
            callbacks.time_units_callback(plotter, monitor, controls, serial_connection)

        controls.time_units.on_change("value", _time_units_callback)

        def _max_cols_callback(attr, old, new):
            callbacks.max_cols_callback(plotter, monitor, controls, serial_connection)

        controls.max_cols.on_change("value", _max_cols_callback)

        def _col_labels_callback(attr, old, new):
            callbacks.col_labels_callback(plotter, monitor, controls, serial_connection)

        controls.col_labels.on_change("value", _col_labels_callback)

        def _rollover_callback(attr, old, new):
            callbacks.rollover_callback(plotter, monitor, controls, serial_connection)

        controls.rollover.on_change("value", _rollover_callback)

        def _glyph_callback(attr, old, new):
            callbacks.glyph_callback(plotter, monitor, controls, serial_connection)

        controls.glyph.on_change("active", _glyph_callback)

        # Define periodic callbacks
        @bokeh.driving.linear()
        def _stream_update(step):
            callbacks.stream_update(plotter, monitor, controls, serial_connection)

        # Have the app killer in here as well
        @bokeh.driving.linear()
        def _port_search_update(step):
            if serial_connection.kill_app:
                sys.exit()

            callbacks.port_search_callback(
                plotter, monitor, controls, serial_connection
            )

        # Add the layout to the app
        doc.add_root(app_layout)

        # Add periodic callbacks to doc
        pc = doc.add_periodic_callback(_stream_update, streamdelay)
        pc_port = doc.add_periodic_callback(_port_search_update, portsearchdelay)

    return _app


def launch(
    port=5006,
    browser=None,
    baudrate=115200,
    maxcols=10,
    delimiter="comma",
    columnlabels="",
    timecolumn=None,
    timeunits="ms",
    rollover=400,
    glyph="lines",
    inputtype="ascii",
    fileprefix="_tmp",
    daqdelay=20,
    streamdelay=90,
    portsearchdelay=1000,
):
    """Launch a serial dashboard.

    Parameters
    ----------
    port : int, default 5006
        Port at localhost for serving dashboard.
    browser : str, default None
        Browser to use for dashboard. If None, uses OS default.
    baudrate : int, default 115200
        Baud rate of serial connection. Allowed values are 300, 1200,
        2400, 4800, 9600, 19200, 38400, 57600, 74880, 115200, 230400,
        250000, 500000, 1000000, 2000000.
    maxcols : int, default 10
        Maximum number of columns of data coming off of the board.
    delimiter : str, default "comma"
        Delimiter of data coming off of the board. Allowed values are
        "comma", "space", "tab", "whitespace", "vertical line",
        "semicolon", "asterisk", "slash"
    columnlabels : str, default ""
        Labels for columnbs using the delimiter specified with
        `delimiter` keyword argument.
    timecolumn : int, default None
        Column (zero-indexed) of incoming data that specifies time
    timeunits : str, default "ms"
        Units of incoming time data. Allowed values are "none", "µs",
        "ms", "s", "min", "hr".
    rollover : int, default 400
        Number of data points to be shown on a plot for each column.
        Allowed values are 100, 200, 400, 800, 1600, 3200.
    glyph : str, default "lines"
        Which glyphs to display in the plotter. Allowed values are
        "lines", "dots", "both".
    inputtype : str, default "ascii"
        Whether input sent to the board is ASCII or bytes. Allowed
        values are "ascii", "bytes".
    fileprefix : str, default "_tmp"
        Prefix for output files
    daqdelay : float, default 20.0
        Roughly the delay in data acquisition from the board in
        milliseconds. The true delay is a bit above 80% of this value.
    streamdelay : int, default 90
        Delay between updates of the plotter and monitor in
        milliseconds.
    portsearchdelay : int, default 1000
        Delay between checks of connected serial devices in
        milliseconds.
    """
    # Build app
    dashboard_app = app(
        baudrate=baudrate,
        maxcols=maxcols,
        delimiter=delimiter,
        columnlabels=columnlabels,
        timecolumn=timecolumn,
        timeunits=timeunits,
        rollover=rollover,
        glyph=glyph,
        inputtype=inputtype,
        fileprefix=fileprefix,
        streamdelay=streamdelay,
        portsearchdelay=portsearchdelay,
    )

    app_dict = {"/serial-dashboard": Application(FunctionHandler(dashboard_app))}
    server = Server(app_dict, port=port)
    server.show("/serial-dashboard", browser=browser)
    server.run_until_shutdown()
