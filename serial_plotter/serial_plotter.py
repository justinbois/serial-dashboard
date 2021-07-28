import asyncio
import re

import numpy as np
import pandas as pd

import serial
import serial.tools.list_ports

import bokeh.plotting
import bokeh.io
import bokeh.layouts
import bokeh.driving

from . import boards
from . import callbacks


def plot():
    """Build a plot of voltage vs time data"""
    # Set up plot area
    p = bokeh.plotting.figure(
        frame_width=600,
        frame_height=175,
        x_axis_label="sample number",
        y_axis_label=" ",
        toolbar_location="above",
        title="serial plotter",
    )

    # No range padding on x: signal spans whole plot
    p.x_range.range_padding = 0

    # We'll sue whitesmoke backgrounds
    p.border_fill_color = "whitesmoke"

    # Define the data source
    source = bokeh.models.ColumnDataSource(data=dict(t=[], V=[]))

    # If we are in streaming mode, use a line, dots for on-demand
    p.line(source=source, x="t", y="V")

    # Put a phantom circle so axis labels show before data arrive
    phantom_source = bokeh.models.ColumnDataSource(
        data=dict(phantom_t=[0], phantom_data=[0])
    )
    p.circle(source=phantom_source, x="phantom_t", y="phantom_data", visible=False)

    return p, source, phantom_source


def monitor():
    """Print text of data coming in"""
    monitor_text = """<div style="background-color: whitesmoke;">
  <p style="margin-left: 50px; margin-bottom: 0px;">
    <b>serial monitor</b>
  </p>
</div>
<div style="border-style: solid; border-width: 10px; border-color: whitesmoke; background-color: white; width: 630px; height: 200px; overflow: scroll;">
  <pre></pre></div>"""

    return bokeh.models.Div(text=monitor_text, background="whitesmoke", width=650)


def controls(serial_dict):
    stream = bokeh.models.Toggle(label="stream", button_type="success", width=100)
    clear = bokeh.models.Button(label="clear", button_type="warning", width=100)
    stream_monitor = bokeh.models.Toggle(
        label="stream", button_type="success", width=100
    )
    clear_monitor = bokeh.models.Button(label="clear", button_type="warning", width=100)
    save = bokeh.models.Button(label="save", button_type="primary", width=100)
    save_notice = bokeh.models.Div(text="<p>No data saved.</p>", width=165)
    file_input = bokeh.models.TextInput(title="file name", value="_tmp.csv", width=165)
    delimiter = bokeh.models.Select(
        title="delimiter",
        value="space",
        options=[
            "space",
            "tab",
            "comma",
            "whitespace",
            "vertical line",
            "semicolon",
            "asterisk",
            "slash",
        ],
    )
    rollover = bokeh.models.Select(
        title="number of points on plot",
        value="400",
        options=["100", "200", "400", "800", "1000", "unlimited"],
    )

    # Set up port selector
    port = bokeh.models.Select(title="port", options=[])

    # Search for available ports and populate options
    callbacks.port_search_callback(port, serial_dict)

    # Set the selected port to the first one
    if len(port.options) > 0:
        serial_dict["port"] = list(serial_dict["available_ports"])[0]
        port.value = serial_dict["port"]

    # Set up baud rate with Arduino defaults
    baudrate = bokeh.models.Select(
        title="baud rate",
        options=[
            "300",
            "1200",
            "2400",
            "4800",
            "9600",
            "19200",
            "38400",
            "57600",
            "74880",
            "115200",
            "230400",
            "250000",
            "500000",
            "1000000",
            "2000000",
        ],
        value="115200",
    )
    callbacks.baudrate_callback(baudrate, serial_dict)

    port_search = bokeh.models.Button(
        label="refresh ports", button_type="primary", width=125
    )
    port_connect = bokeh.models.Button(
        label="connect", button_type="success", width=125
    )

    port_status = bokeh.models.Div(
        text="<p><b>port status:</b> disconnected</p>", width=200
    )
    serial_dict["port_status"] == "disconnected"

    line_ending = bokeh.models.Select(
        title="line ending",
        value="Newline",
        options=["No line ending", "Newline", "Carriage return", "Both NL & CR"],
    )
    time_column = bokeh.models.Select(
        title="time column",
        value="None",
        options=["None", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    )
    time_units = bokeh.models.Select(
        title="time units", value="None", options=["None", "µs", "ms", "s", "min", "hr"]
    )
    input_window = bokeh.models.TextInput(title="input", value="", width=180)
    ascii_bytes = bokeh.models.RadioGroup(labels=["ascii", "bytes"], active=0)

    return dict(
        stream=stream,
        clear=clear,
        stream_monitor=stream_monitor,
        clear_monitor=clear_monitor,
        save=save,
        save_notice=save_notice,
        file_input=file_input,
        delimiter=delimiter,
        rollover=rollover,
        port=port,
        port_search=port_search,
        baudrate=baudrate,
        port_connect=port_connect,
        port_status=port_status,
        line_ending=line_ending,
        time_column=time_column,
        time_units=time_units,
        input_window=input_window,
        ascii_bytes=ascii_bytes,
    )


def layout(p, mon, ctrls):
    plotter_buttons = bokeh.layouts.column(
        bokeh.models.Spacer(height=50),
        ctrls["stream"],
        bokeh.models.Spacer(height=50),
        ctrls["clear"],
    )
    plotter_layout = bokeh.layouts.row(
        p,
        bokeh.models.Spacer(width=10),
        plotter_buttons,
        bokeh.models.Spacer(width=15),
        spacing=10,
        margin=(30, 30, 30, 30),
        background="whitesmoke",
    )

    input_layout = bokeh.layouts.row(
        ctrls["input_window"],
        bokeh.models.Spacer(width=20),
        bokeh.layouts.column(bokeh.models.Spacer(height=15), ctrls["ascii_bytes"]),
    )

    specs = bokeh.layouts.column(
        ctrls["port"],
        ctrls["baudrate"],
        bokeh.layouts.row(ctrls["port_search"], ctrls["port_connect"]),
        ctrls["port_status"],
        bokeh.models.Spacer(height=40),
        ctrls["delimiter"],
        bokeh.models.Spacer(height=10),
        ctrls["line_ending"],
        bokeh.models.Spacer(height=10),
        ctrls["time_column"],
        bokeh.models.Spacer(height=10),
        ctrls["time_units"],
        bokeh.models.Spacer(height=10),
        ctrls["rollover"],
        bokeh.models.Spacer(height=40),
        input_layout,
        width=200,
    )

    monitor_buttons = bokeh.layouts.column(
        bokeh.models.Spacer(height=50),
        ctrls["stream_monitor"],
        bokeh.models.Spacer(height=50),
        ctrls["clear_monitor"],
    )
    monitor_layout = bokeh.layouts.row(
        mon,
        bokeh.models.Spacer(width=10),
        monitor_buttons,
        bokeh.models.Spacer(width=15),
        spacing=10,
        margin=(30, 30, 30, 30),
        background="whitesmoke",
    )

    return bokeh.layouts.row(
        bokeh.layouts.column(plotter_layout, monitor_layout),
        bokeh.layouts.column(bokeh.models.Spacer(height=10), specs),
    )


def find_board(port=None, quiet=True):
    """Get the name of the port that is connected to the board.

    Parameters
    ----------
    port : str, default None
        If str, address of port to which board is connected. If None,
        attempts to find a connected board.
    quiet : bool, default True
        If True, do not report port/board name to screen. Otherwise,
        print that information.

    Returns
    -------
    output : str
        Returns the address of port to which the board is connected.
        `None` is returned if no board is found.

    """
    if port is None:
        my_ports = []
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if p.hwid is not None:
                try:
                    i = p.hwid.find("VID:PID=") + 8
                    j = p.hwid.find(" ", i)
                    vid_pid = p.hwid[i:j]
                    if vid_pid in vid_pid_boards:
                        my_ports.append([p.device, vid_pid_boards[vid_pid], vid_pid])
                except:
                    pass

        if len(my_ports) > 1:
            raise RuntimeError(
                "Found more that one port. Called `find_board()` with a single `port` argument to choose which one you want to use. The found ports were:\n",
                my_ports,
            )
        elif len(my_ports) == 0:
            raise RuntimeError("Failed to find any known boards.")
        else:
            if not quiet:
                print(
                    "Found board "
                    + my_ports[0][1]
                    + " with VID:PID "
                    + my_ports[0][2]
                    + " at port "
                    + my_ports[0][0]
                    + "."
                )
            port = my_ports[0][0]

    return port


def read_all(ser, read_buffer=b"", **args):
    """Read all available bytes from the serial port
    and append to the read buffer.

    Parameters
    ----------
    ser : serial.Serial() instance
        The device we are reading from.
    read_buffer : bytes, default b''
        Previous read buffer that is appended to.

    Returns
    -------
    output : bytes
        Bytes object that contains read_buffer + read.

    Notes
    -----
    .. `**args` appears, but is never used. This is for
       compatibility with `read_all_newlines()` as a
       drop-in replacement for this function.
    """
    # Set timeout to None to make sure we read all bytes
    previous_timeout = ser.timeout
    ser.timeout = None

    in_waiting = ser.in_waiting
    read = ser.read(size=in_waiting)

    # Reset to previous timeout
    ser.timeout = previous_timeout

    return read_buffer + read


def read_all_newlines(ser, read_buffer=b"", n_reads=1):
    """Read data in until encountering newlines.

    Parameters
    ----------
    ser : serial.Serial() instance
        The device we are reading from.
    n_reads : int
        The number of reads up to newlines
    read_buffer : bytes, default b''
        Previous read buffer that is appended to.

    Returns
    -------
    output : bytes
        Bytes object that contains read_buffer + read.

    Notes
    -----
    .. This is a drop-in replacement for read_all().
    """
    raw = read_buffer
    for _ in range(n_reads):
        raw += ser.read_until()

    return raw


def time_in_ms(t, time_units):
    if t.isdecimal():
        t = int(t)
    else:
        t = float(t)

    if time_units == "ms":
        return t
    elif time_units == "s":
        return t * 1000
    elif time_units == "µs":
        return t / 1000 if t % 1000 else t // 1000
    elif time_units == "min":
        return t * 60000
    elif time_units == "hr":
        return t * 360000


def parse_read(read, sep=" ", time_column=None, time_units="ms", n_reads=0):
    """Parse a read with time, voltage data

    Parameters
    ----------
    read : byte string
        Byte string with comma delimited time/voltage
        measurements.
    sep : str, default ' '
        Character separating columns of written data.
    time_column : int, default None
        If int, the index of the column of read-in data that contains
        the time in milliseconds. If None, then no time is read in, and
        the read number is stored in the `time_ms` output.
    time_units : str, default "ms"
        One of [None, 'µs', 'ms', 's', 'min', 'hr']. All times are
        converted to milliseconds, except for None, which is only
        allowed when time_column is None.
    n_reads : int, default 0
        The number of reads that have previously been read in.

    Returns
    -------
    time_ms : list of ints
        Time points in milliseconds or read number if time_column is
        None.
    data : list of ints
        All non-time data read in.
    n_reads : int
        Updated number of records read.
    remaining_bytes : byte string
        Remaining, unparsed bytes.
    """
    time_ms = []
    data = []

    # Separate independent time/voltage measurements
    pattern = re.compile(bytes("\d+|" + sep, "ascii"))
    raw_list = [b"".join(pattern.findall(raw)).decode() for raw in read.split(b"\r\n")]

    for raw in raw_list[:-1]:
        try:
            read_data = raw.split(sep)
            data.append(
                [
                    int(datum) if datum.isdecimal() else float(datum)
                    for datum in read_data
                ]
            )
            if time_column is None:
                time_ms.append(n_reads)
            else:
                time_ms.append(time_in_ms(read_data.pop(time_column), time_units))
            n_reads += 1
        except:
            pass

    if len(raw_list) == 0:
        return time_ms, data, n_reads, b""
    else:
        return time_ms, data, n_reads, raw_list[-1].encode()


def populate_glyphs(data):
    # Define the data source
    data_dict = {"data" + str(i): [] for i in range(n_data)}
    data_dict["t"] = []
    source = bokeh.models.ColumnDataSource(data=data_dict)

    # Populate glyphs
    for i in range(n_data):
        p.line(source=source, x="t", y="data" + str(i))


def stream_callback(ser, plot_data, new):
    if new:
        plot_data["mode"] = "stream"
    else:
        plot_data["mode"] = "ignore"

    ser.reset_input_buffer()


def reset_callback(mode, data, source, phantom_source, controls):
    # Turn off the stream
    if mode == "stream":
        controls["acquire"].active = False

    # Black out the data dictionaries
    data["t"] = []
    data["V"] = []

    # Reset the sources
    source.data = dict(t=[], V=[])
    phantom_source.data = dict(t=[0], V=[0])


async def daq_stream_async(
    ser, plot_data, monitor_data, delay=20, n_reads_per_chunk=1, reader=read_all,
):
    """Obtain streaming data"""
    # Receive data
    read_buffer = [b""]
    while True:
        # Read in chunk of data
        raw = reader(ser, read_buffer=read_buffer[0], n_reads=n_reads_per_chunk)

        if plot_data["streaming"]:
            # Parse it, passing if it is gibberish
            try:
                t, V, read_buffer[0] = parse_read(raw)

                # Update data dictionary
                data["t"] += t
                data["V"] += V
            except:
                pass

        if monitor_data["streaming"]:
            monitor_data["data"] += raw.decode()

        # Sleep 80% of the time before we need to start reading chunks
        await asyncio.sleep(0.8 * n_reads_per_chunk * delay / 1000)


def plot_update(plot_data, source, phantom_source, rollover):
    # Update plot by streaming in data
    new_data = {
        "t": np.array(data["t"][data["prev_array_length"] :]) / 1000,
        "V": data["V"][data["prev_array_length"] :],
    }
    source.stream(new_data, rollover)

    # Adjust new phantom data point if new data arrived
    if len(new_data["t"] > 0):
        phantom_source.data = dict(t=[new_data["t"][-1]], V=[new_data["V"][-1]])
    data["prev_array_length"] = len(data["t"])


def app():
    def _app(doc):
        # "Global" variables
        serial_dict = dict(
            ser=None,
            port=None,
            baudrate=None,
            available_ports=dict(),
            reverse_available_ports=dict(),
            port_status="disconnected",
        )
        plot_data = dict(prev_array_length=0, t=[], data=[], streaming=False)
        monitor_data = dict(data=[], streaming=False)

        p, source, phantom_source = plot()
        mon = monitor()
        ctrls = controls(serial_dict)
        app_layout = layout(p, mon, ctrls)

        def _port_select_callback(attr, old, new):
            callbacks.port_select_callback(ctrls["port"], serial_dict)

        def _port_search_callback(event=None):
            callbacks.port_search_callback(ctrls["port"], serial_dict)

        def _port_connect_callback(event=None):
            callbacks.port_connect_callback(ctrls["port_status"], serial_dict)

        def _baudrate_callback(attr, old, new):
            callbacks.baudrate_callback(ctrls["baudrate"], serial_dict)

        def _input_window_callback(attr, old, new):
            callbacks.input_window_callback(
                ctrls["input_window"], ctrls["ascii_bytes"], serial_dict["ser"]
            )

        # @bokeh.driving.linear()
        # def _stream_update(step):
        #     stream_update(plot_data, stream_source, stream_phantom_source, rollover)

        # Link callbacks
        ctrls["port"].on_change("value", _port_select_callback)
        ctrls["port_search"].on_click(_port_search_callback)
        ctrls["port_connect"].on_click(_port_connect_callback)
        ctrls["baudrate"].on_change("value", _baudrate_callback)
        ctrls["input_window"].on_change("value", _input_window_callback)

        # Add the layout to the app
        doc.add_root(app_layout)

    return _app
