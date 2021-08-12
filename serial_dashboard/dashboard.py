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

from . import boards
from . import callbacks
from . import comms


class SerialConnection(object):
    def __init__(self):
        """Create an instance storing information about a serial
        connection."""
        self.ser = None
        self.port = None
        self.baudrate = 115200
        self.ports = []
        self.available_ports = dict()
        self.reverse_available_ports = dict()
        self.port_status = "disconnected"
        self.daq_task = None
        self.port_search_task = None
        self.kill_app = False


class Controls(object):
    def __init__(self):
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
            title="file name", value="_tmp.csv", width=150, visible=False
        )

        self.plot_write = bokeh.models.Button(
            label="save", button_type="primary", width=50, visible=False
        )

        self.plot_save_notice = bokeh.models.Div(
            text='<p style="font-size: 8pt;">No data saved.</p>', width=100
        )

        self.monitor_save = bokeh.models.Button(
            label="save", button_type="primary", width=100
        )

        self.monitor_file_input = bokeh.models.TextAreaInput(
            title="file name", value="_tmp.txt", width=150, visible=False
        )

        self.monitor_write = bokeh.models.Button(
            label="save", button_type="primary", width=50, visible=False
        )

        self.monitor_save_notice = bokeh.models.Div(
            text='<p style="font-size: 8pt;">No data saved.</p>', width=100
        )

        self.delimiter = bokeh.models.Select(
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

        self.rollover = bokeh.models.Select(
            title="plot rollover",
            value="400",
            options=["100", "200", "400", "800", "1600", "3200"],
            width=100,
        )

        self.max_cols = bokeh.models.Spinner(
            title="maximum number of columns",
            value=10,
            low=1,
            high=10,
            step=1,
            width=100,
        )

        self.col_labels = bokeh.models.TextInput(
            title="column labels", value="", width=200
        )

        # Set up port selector
        self.port = bokeh.models.Select(title="port", options=[], value="", width=200,)

        # Set up baud rate with Arduino defaults
        self.baudrate = bokeh.models.Select(
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
            value="none",
            options=["none", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            width=100,
        )

        self.time_units = bokeh.models.Select(
            title="time units",
            value="ms",
            options=["none", "µs", "ms", "s", "min", "hr"],
            width=100,
        )

        self.input_window = bokeh.models.TextAreaInput(
            title="input", value="", width=150
        )

        self.input_send = bokeh.models.Button(
            label="send", button_type="primary", width=50, disabled=True
        )

        self.ascii_bytes = bokeh.models.RadioGroup(labels=["ascii", "bytes"], active=0)

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
    def __init__(self):
        """Create a serial plotter."""
        self.prev_data_length = 0
        self.data = []
        self.time_column = None
        self.time_units = "ms"
        self.max_cols = 10
        self.col_labels = [str(col) for col in range(10)]
        self.streaming = False
        self.sources = []
        self.delimiter = ","
        self.lines = None
        self.dots = None
        self.rollover = 400
        self.plot, self.legend, self.phantom_source = self.base_plot()

    def base_plot(self):
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


class SerialMonitor(object):
    def __init__(self, scroll_snap=True):
        """Create a serial monitor."""
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
        # mouse scrolling directions will be reversed from their usual.
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


def layout(plotter, monitor, controls):
    """Build layout of serial dashboard."""
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
        plotter_buttons, plotter.plot, margin=(30, 0, 0, 0), background="whitesmoke",
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
            bokeh.models.Spacer(height=20),
            bokeh.layouts.row(
                input_layout, bokeh.models.Spacer(width=100), shutdown_layout,
            ),
            plotter_layout,
            monitor_layout,
        ),
    )


def app():
    """Returns a function that can be used as a Bokeh app.

    The app can be launched using `bokeh serve --show appscript.py`,
    from the command line where the contents of `appscript.py` are:

    ```
    import bokeh.plotting
    import serial_dashboard

    app = serial_dashboard.app()

    app(bokeh.plotting.curdoc())
    ```

    To launch the app programmatically with Python, do the following:

    ```
    from bokeh.server.server import Server
    from bokeh.application import Application
    from bokeh.application.handlers.function import FunctionHandler
    import serial_dashboard

    app = serial_dashboard.app()

    app_dict = {'/serial-dashboard': Application(FunctionHandler(app))}
    server = Server(app_dict, port=5006)
    server.show('/serial-dashboard')
    server.run_until_shutdown()
    ```
    """

    def _app(doc):
        # "Global" variables
        serial_connection = SerialConnection()
        controls = Controls()
        plotter = SerialPlotter()
        monitor = SerialMonitor()

        app_layout = layout(plotter, monitor, controls)

        # Start port sniffer
        serial_connection.port_search_task = asyncio.create_task(
            comms.port_search_async(serial_connection)
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
        pc = doc.add_periodic_callback(_stream_update, 90)
        pc_port = doc.add_periodic_callback(_port_search_update, 1000)

    return _app


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
