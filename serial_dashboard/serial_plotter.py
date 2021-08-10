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
from . import comms


def plot():
    """Build a plot of voltage vs time data"""
    # Set up plot area
    p = bokeh.plotting.figure(
        frame_width=600,
        frame_height=175,
        x_axis_label="sample_number",
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
    p.circle(source=phantom_source, x="phantom_t", y="phantom_y", visible=False)

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


def monitor():
    """Print text of data coming in"""

    # Use CSS scroll-snap to enable scrolling with default at bottom
    base_monitor_text = """<style>
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
    # mouse scrolling directions will be reversed from their usual.
    # This method may be useful for older browsers that do not have
    # CSS scroll-snap.
    alternative_base_monitor_text = """<style>
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

    return bokeh.models.Div(
        text=base_monitor_text,
        background="whitesmoke",
        height=250,
        width=650,
        sizing_mode="fixed",
    )


def controls(serial_dict):
    plot_stream = bokeh.models.Toggle(label="stream", button_type="success", width=100)
    plot_clear = bokeh.models.Button(label="clear", button_type="warning", width=100)
    monitor_stream = bokeh.models.Toggle(
        label="stream", button_type="success", width=100
    )
    monitor_clear = bokeh.models.Button(label="clear", button_type="warning", width=100)
    save = bokeh.models.Button(label="save", button_type="primary", width=100)
    save_notice = bokeh.models.Div(text="<p>No data saved.</p>", width=165)
    file_input = bokeh.models.TextInput(title="file name", value="_tmp.csv", width=165)
    delimiter = bokeh.models.Select(
        title="delimiter",
        value="comma",
        options=[
            "comma",
            "space",
            "tab",
            "whitespace",
            "vertical line",
            "semicolon",
            "asterisk",
            "slash",
        ],
        width=100,
    )
    rollover = bokeh.models.Select(
        title="plot rollover",
        value="400",
        options=["100", "200", "400", "800", "1600", "3200"],
        width=100,
    )
    max_cols = bokeh.models.Spinner(
        title="max columns in input", value=10, low=1, high=10, step=1, width=100,
    )
    col_labels = bokeh.models.TextInput(title="column labels", value="", width=200)

    # Set up port selector
    port = bokeh.models.Select(title="port", options=[], value="", width=200,)

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
        width=100,
    )
    callbacks.baudrate_callback(baudrate, serial_dict)

    port_connect = bokeh.models.Button(
        label="connect", button_type="success", width=100
    )
    port_disconnect = bokeh.models.Button(
        label="disconnect", button_type="danger", width=100, disabled=True
    )

    port_status = bokeh.models.Div(
        text="<p><b>port status:</b> disconnected</p>", width=200
    )
    serial_dict["port_status"] == "disconnected"

    time_column = bokeh.models.Select(
        title="time column",
        value="None",
        options=["None", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        width=100,
    )
    time_units = bokeh.models.Select(
        title="time units",
        value="ms",
        options=["None", "µs", "ms", "s", "min", "hr"],
        width=100,
    )
    input_window = bokeh.models.TextInput(title="input", value="", width=150)
    ascii_bytes = bokeh.models.RadioGroup(labels=["ascii", "bytes"], active=0)

    return dict(
        plot_stream=plot_stream,
        plot_clear=plot_clear,
        monitor_stream=monitor_stream,
        monitor_clear=monitor_clear,
        save=save,
        save_notice=save_notice,
        file_input=file_input,
        delimiter=delimiter,
        rollover=rollover,
        port=port,
        baudrate=baudrate,
        port_connect=port_connect,
        port_disconnect=port_disconnect,
        port_status=port_status,
        time_column=time_column,
        max_cols=max_cols,
        col_labels=col_labels,
        time_units=time_units,
        input_window=input_window,
        ascii_bytes=ascii_bytes,
    )


def layout(p, mon, ctrls):
    plotter_buttons = bokeh.layouts.column(
        bokeh.models.Spacer(height=50),
        ctrls["plot_stream"],
        bokeh.models.Spacer(height=50),
        ctrls["plot_clear"],
    )
    plotter_layout = bokeh.layouts.row(
        plotter_buttons,
        bokeh.models.Spacer(width=15),
        p,
        bokeh.models.Spacer(width=10),
        margin=(30, 0, 30, 0),
        background="whitesmoke",
    )

    input_layout = bokeh.layouts.row(
        bokeh.models.Spacer(width=10),
        ctrls["input_window"],
        bokeh.models.Spacer(width=20),
        bokeh.layouts.column(bokeh.models.Spacer(height=15), ctrls["ascii_bytes"]),
        background="whitesmoke",
        width=300,
    )

    port_controls = bokeh.layouts.column(
        ctrls["port"],
        ctrls["baudrate"],
        bokeh.models.Spacer(height=10),
        ctrls["port_connect"],
        ctrls["port_disconnect"],
        ctrls["port_status"],
        background="whitesmoke",
    )

    specs = bokeh.layouts.column(
        ctrls["delimiter"],
        bokeh.models.Spacer(height=10),
        ctrls["max_cols"],
        bokeh.models.Spacer(height=10),
        ctrls["col_labels"],
        bokeh.models.Spacer(height=10),
        ctrls["time_column"],
        bokeh.models.Spacer(height=10),
        ctrls["time_units"],
        bokeh.models.Spacer(height=10),
        ctrls["rollover"],
        background="whitesmoke",
    )

    monitor_buttons = bokeh.layouts.column(
        bokeh.models.Spacer(height=50),
        ctrls["monitor_stream"],
        bokeh.models.Spacer(height=50),
        ctrls["monitor_clear"],
    )
    monitor_layout = bokeh.layouts.row(
        monitor_buttons,
        bokeh.models.Spacer(width=15),
        mon,
        bokeh.models.Spacer(width=10),
        margin=(30, 0, 30, 0),
        background="whitesmoke",
    )

    return bokeh.layouts.row(
        bokeh.layouts.column(port_controls, bokeh.models.Spacer(height=30), specs),
        bokeh.models.Spacer(width=20),
        bokeh.layouts.column(
            bokeh.models.Spacer(height=20), input_layout, plotter_layout, monitor_layout
        ),
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


def app():
    def _app(doc):
        # "Global" variables
        serial_dict = dict(
            ser=None,
            port=None,
            baudrate=None,
            ports=[],
            available_ports=dict(),
            reverse_available_ports=dict(),
            port_status="disconnected",
            daq_task=None,
            port_search_task=None,
        )

        p, legend, phantom_source = plot()
        mon = monitor()
        ctrls = controls(serial_dict)
        app_layout = layout(p, mon, ctrls)

        plot_data = dict(
            prev_data_length=0,
            data=np.array([]),
            time_column=None,
            time_units="ms",
            max_cols=10,
            col_labels=[str(col) for col in range(10)],
            streaming=False,
            sources=[],
            phantom_source=phantom_source,
            legend=legend,
            delimiter=",",
            lines=None,
            dots=None,
        )
        monitor_data = dict(prev_data_length=0, data=[], streaming=False)

        # Store the base text for clearing
        monitor_data["base_text"] = mon.text

        # Start port sniffer
        serial_dict["port_search_task"] = asyncio.create_task(
            comms.port_search_async(ctrls["port"], serial_dict)
        )

        def _port_select_callback(attr, old, new):
            callbacks.port_select_callback(ctrls["port"], serial_dict)

        def _port_connect_callback(event=None):
            callbacks.port_connect_callback(
                ctrls["port_connect"],
                ctrls["port_disconnect"],
                ctrls["port"],
                ctrls["baudrate"],
                ctrls["max_cols"],
                ctrls["port_status"],
                serial_dict,
                plot_data,
                monitor_data,
                p,
            )

        def _port_disconnect_callback(event=None):
            callbacks.port_disconnect_callback(
                ctrls["port_connect"],
                ctrls["port_disconnect"],
                ctrls["port"],
                ctrls["baudrate"],
                ctrls["max_cols"],
                ctrls["port_status"],
                serial_dict,
            )

        def _baudrate_callback(attr, old, new):
            callbacks.baudrate_callback(ctrls["baudrate"], serial_dict)

        def _input_window_callback(attr, old, new):
            if new != "":
                callbacks.input_window_callback(
                    ctrls["input_window"], ctrls["ascii_bytes"], serial_dict["ser"]
                )

        def _monitor_stream_callback(event=None):
            callbacks.monitor_stream_callback(ctrls["monitor_stream"], monitor_data)

        def _monitor_clear_callback(event=None):
            callbacks.monitor_clear_callback(mon, monitor_data)

        def _plot_stream_callback(event=None):
            callbacks.plot_stream_callback(ctrls["plot_stream"], plot_data)

        def _plot_clear_callback(event=None):
            callbacks.plot_clear_callback(p, plot_data)

        def _time_units_callback(attr, old, new):
            callbacks.time_units_callback(
                ctrls["time_units"], ctrls["time_column"], p, plot_data
            )

        def _time_column_callback(attr, old, new):
            callbacks.time_column_callback(
                ctrls["time_column"], ctrls["time_units"], p, plot_data
            )

        def _max_cols_callback(attr, old, new):
            callbacks.max_cols_callback(ctrls["max_cols"], plot_data)

        def _col_labels_callback(attr, old, new):
            callbacks.col_labels_callback(ctrls["col_labels"], plot_data)

        def _delimiter_select_callback(attr, old, new):
            callbacks.delimiter_select_callback(ctrls["delimiter"], plot_data)

        @bokeh.driving.linear()
        def _stream_update(step):
            callbacks.stream_update(
                p, mon, plot_data, monitor_data, int(ctrls["rollover"].value),
            )

        @bokeh.driving.linear()
        def _port_search_update(step):
            callbacks.port_search_callback(ctrls["port"], serial_dict)

        # Link callbacks
        ctrls["port"].on_change("value", _port_select_callback)
        ctrls["port_connect"].on_click(_port_connect_callback)
        ctrls["port_disconnect"].on_click(_port_disconnect_callback)
        ctrls["baudrate"].on_change("value", _baudrate_callback)
        ctrls["input_window"].on_change("value", _input_window_callback)
        ctrls["monitor_stream"].on_click(_monitor_stream_callback)
        ctrls["monitor_clear"].on_click(_monitor_clear_callback)
        ctrls["plot_clear"].on_click(_plot_clear_callback)
        ctrls["plot_stream"].on_click(_plot_stream_callback)
        ctrls["delimiter"].on_change("value", _delimiter_select_callback)
        ctrls["time_column"].on_change("value", _time_column_callback)
        ctrls["max_cols"].on_change("value", _max_cols_callback)
        ctrls["col_labels"].on_change("value", _col_labels_callback)
        ctrls["time_units"].on_change("value", _time_units_callback)

        # Add the layout to the app
        doc.add_root(app_layout)

        # Add a periodic callback, monitor changes in stream data
        pc = doc.add_periodic_callback(_stream_update, 90)
        pc_port = doc.add_periodic_callback(_port_search_update, 1000)

    return _app
