import asyncio
import copy

import serial
import numpy as np

import bokeh.models

from . import comms

# Color palette is from colorcet
colors = [
    "#1f77b3",
    "#ff7e0e",
    "#2ba02b",
    "#d62628",
    "#9367bc",
    "#8c564b",
    "#e277c1",
    "#7e7e7e",
    "#bcbc21",
    "#16bdcf",
]


def populate_glyphs(p, plot_data, colors=colors):
    # Define the data sources
    plot_data["sources"] = [
        bokeh.models.ColumnDataSource(data=dict(t=[], y=[]))
        for _ in range(plot_data["max_cols"])
    ]

    # Lines
    plot_data["lines"] = [
        p.line(source=source, x="t", y="y", color=color)
        for color, source in zip(colors[: plot_data["max_cols"]], plot_data["sources"])
    ]
    plot_data["dots"] = [
        p.circle(source=source, x="t", y="y", color=color, size=3)
        for color, source in zip(colors[: plot_data["max_cols"]], plot_data["sources"])
    ]

    # Start with just lines visible
    for i, _ in enumerate(plot_data["dots"]):
        plot_data["dots"][i].visible = False

    # Make a legend
    active_col_labels = [
        x
        for i, x in enumerate(plot_data["col_labels"])
        if i != plot_data["time_column"]
    ]

    plot_data["legend"].items = [
        bokeh.models.LegendItem(label=col_label, renderers=[line], index=col)
        for col, (col_label, line) in enumerate(
            zip(active_col_labels, plot_data["lines"])
        )
    ]

    # Make legend visible
    p.legend.visible = True


def fill_nans(x, ncols):
    """Right-fill NaNs into an array so that each row has the same
    number of entries.

    Parameters
    ----------
    x : list of lists
        Array with potentially unequal row lengths to be filled.
    ncols : int
        Number of columns we wish to achieve after filling NaNs. We fill
        to the larger of the maximum row length of `x` and `ncols`.

    Returns
    -------
    output : Numpy array
        Return a 2D Numpy array with all rows having the same number
        of columns, padded with NaNs. The exception is if the input is
        an empty list and `ncols` is zero, in which case np.array([]) is
        returned.

    Notes
    -----
    .. `x` is modified in place. Do not use this function if you want
       `x` back.
    .. There is no type-checking on `x`. It must be a list of lists.
    """
    if len(x) == 0:
        if ncols > 0:
            out = np.empty((1, ncols))
            out.fill(np.nan)
            return out, ncols
        else:
            return np.array([]), 0

    # Find number of columns in this incoming data
    ncols = max(ncols, max([len(row) for row in x]))

    # Fill in incoming data with NaNs so each row has same length
    for i, row in enumerate(x):
        x[i] += [np.nan] * (ncols - len(row))

    # Convert incoming data to a Numpy array
    return np.array(x), ncols


def data_to_dicts(data, max_cols, time_col, time_units, starting_time_ind):
    """Take in data as a list of lists and converts to a list of
    dictionaries that can be used to stream into the ColumnDataSources.
    """
    data, ncols = fill_nans(copy.copy(data), 0)
    if len(data) == 0 or ncols == 0:
        return [dict(t=[], y=[]) for _ in range(ncols)]

    ts = []
    ys = []
    if time_col is None:
        t = starting_time_ind + np.arange(len(data))
        for j in range(min(data.shape[1], max_cols)):
            new_t = []
            new_y = []
            for i, row in enumerate(data):
                if not np.isnan(row[j]):
                    new_t.append(t[i])
                    new_y.append(row[j])
            ts.append(new_t)
            ys.append(new_y)
    elif time_col > ncols:
        return [dict(t=[], y=[]) for _ in range(ncols)]
    else:
        t = data[:, time_col]

        # Return nothing if all nans
        if np.isnan(t).all():
            return [dict(t=[], y=[]) for _ in range(ncols)]

        if time_units == "µs":
            t = t / 1e6
        elif time_units == "ms":
            t = t / 1000

        for j in range(min(data.shape[1], max_cols)):
            if j != time_col:
                new_t = []
                new_y = []
                for i, row in enumerate(data):
                    if not np.isnan(row[j]) and not np.isnan(t[i]):
                        new_t.append(t[i])
                        new_y.append(row[j])
                ts.append(new_t)
                ys.append(new_y)

    return [dict(t=t, y=y) for t, y in zip(ts, ys)]


def stream_update(plot, monitor, plot_data, monitor_data, rollover):
    if monitor_data["streaming"]:
        monitor.text = (
            monitor.text[:-18]
            + "".join(monitor_data["data"][monitor_data["prev_data_length"] :])
            + "</pre></div></div>"
        )

        monitor_data["prev_data_length"] = len(monitor_data["data"])

    # Update plot by streaming in data
    if plot_data["streaming"]:
        ty_dicts = data_to_dicts(
            plot_data["data"][plot_data["prev_data_length"] :],
            plot_data["max_cols"],
            plot_data["time_column"],
            plot_data["time_units"],
            plot_data["prev_data_length"],
        )

        for i, ty_dict in enumerate(ty_dicts):
            plot_data["sources"][i].stream(ty_dict, rollover)

        # Adjust new phantom data point if new data arrived
        if len(plot_data["sources"][0].data["t"]) > 0:
            plot_data["phantom_source"].data = dict(
                t=[plot_data["sources"][0].data["t"][-1]],
                y=[plot_data["sources"][0].data["y"][-1]],
            )

        # Reset the array length
        plot_data["prev_data_length"] = len(plot_data["data"])


def port_search_callback(port_select, serial_dict):
    """Update available ports"""
    if port_select.options != list(serial_dict["reverse_available_ports"].keys()):
        port_select.options = list(serial_dict["reverse_available_ports"].keys())

        # Set the port to the first option if not already set
        if port_select.value is None or port_select.value == "":
            port_select.value = port_select.options[0]


def port_select_callback(port_select, serial_dict):
    """Store the selected port"""
    serial_dict["port"] = serial_dict["reverse_available_ports"][port_select.value]


def baudrate_callback(baudrate_select, serial_dict):
    """Store the selected baudrate"""
    serial_dict["baudrate"] = baudrate_select.value


def port_connect_callback(
    port_connect,
    port_disconnect,
    port_select,
    baudrate_select,
    max_cols_select,
    port_status,
    input_send,
    serial_dict,
    plot_data,
    monitor_data,
    p,
):
    """Connect to a port"""
    # First shut down port searching
    serial_dict["port_search_task"].cancel()
    serial_dict["port_search_task"] = None

    try:
        # Close the connection if open
        if serial_dict["ser"] is not None:
            try:
                serial_dict["ser"].close()
                serial_dict["ser"] = None
            except:
                pass

        # Give message that connection is being established
        # (Won't show up because still inside Bokeh's event loop; to be fixed.)
        serial_dict["port_status"] = "establishing"
        port_status_callback(port_status, serial_dict)

        # Open the connection and handshake with the serial device
        serial_dict["ser"] = serial.Serial(
            serial_dict["port"], baudrate=serial_dict["baudrate"]
        )
        comms.handshake_board(serial_dict["ser"])

        # Start DAQ
        serial_dict["daq_task"] = asyncio.create_task(
            comms.daq_stream_async(
                serial_dict["ser"],
                plot_data,
                monitor_data,
                delay=20,
                n_reads_per_chunk=1,
                reader=comms.read_all,
            )
        )

        # Set up ColumnDataSources and populate glyphs for the plot
        populate_glyphs(p, plot_data)

        # Disable port selectors now that we're connected
        port_connect.disabled = True
        port_select.disabled = True
        baudrate_select.disabled = True

        # Disable choice of mximum columns in input
        max_cols_select.disabled = True

        # Enable disconnecting
        port_disconnect.disabled = False

        # Enable sending data
        input_send.disabled = False

        #  Update status
        serial_dict["port_status"] = "connected"
        port_status_callback(port_status, serial_dict)
    except:
        serial_dict["port_status"] = "failed"
        serial_dict["ser"] = None
        port_status_callback(port_status, serial_dict)
        try:
            serial_dict["daq_task"].cancel()
        except:
            pass


def port_disconnect_callback(
    port_connect,
    port_disconnect,
    port_select,
    baudrate_select,
    max_cols_select,
    port_status,
    input_send,
    serial_dict,
):
    """Disconnect serial device."""
    # Shut down DAQ task
    serial_dict["daq_task"].cancel()
    serial_dict["daq_task"] = None

    # Close connection
    serial_dict["ser"].close()

    # Re-enable buttons
    port_connect.disabled = False
    port_select.disabled = False
    baudrate_select.disabled = False
    max_cols_select.disabled = False

    # Disable disconnecting
    port_disconnect.disabled = True
    input_send.disabled = True

    # Start port sniffer
    serial_dict["port_search_task"] = asyncio.create_task(
        comms.port_search_async(port_select, serial_dict)
    )

    # Update port status
    serial_dict["port_status"] = "disconnected"
    port_status_callback(port_status, serial_dict)


def port_status_callback(port_status, serial_dict):
    """Update port status text"""
    if serial_dict["port_status"] == "disconnected":
        port_status.text = "<p><b>port status:</b> disconnected</p>"
    elif serial_dict["port_status"] == "establishing":
        port_status.text = f"<p><b>port status:</b> establishing connection to {serial_dict['port']}...</p>"
    elif serial_dict["port_status"] == "connected":
        port_status.text = (
            f"<p><b>port status:</b> connected to {serial_dict['port']}.</p>"
        )
    elif serial_dict["port_status"] == "failed":
        pass
        port_status.text = f'<p><b>port status:</b> <font style="color: tomato;">unable to connect to {serial_dict["port"]}.</font></p>'


def plot_stream_callback(plot_stream_toggle, plot_data):
    plot_data["streaming"] = plot_stream_toggle.active


def plot_clear_callback(plot, plot_data):
    plot_data["data"] = np.array([])
    for i in range(len(plot_data["sources"])):
        plot_data["sources"][i].data = {key: [] for key in plot_data["sources"][i].data}
    plot_data["phantom_source"].data = dict(phantom_t=[0], phantom_y=[0])


def monitor_stream_callback(monitor_stream_toggle, monitor_data):
    monitor_data["streaming"] = monitor_stream_toggle.active


def monitor_clear_callback(monitor, monitor_data):
    monitor_data["data"] = ""
    monitor.text = monitor_data["base_text"]


def adjust_time_axis_label(time_column_select, time_units_select, p):
    if time_units_select.value in ("µs", "ms", "s"):
        p.xaxis.axis_label = "time (s)"
    elif time_units_select.value == "None":
        if plot_data["time_column"] is None:
            p.xaxis.axis_label = "sample number"
        else:
            p.xaxis.axis_label = "time"
    else:
        p.xaxis.axis_label = f"time ({time_units_select.value})"


def time_column_callback(time_column_select, time_units_select, p, plot_data):
    adjust_time_axis_label(time_column_select, time_units_select, p)

    if time_column_select.value == "None":
        plot_data["time_column"] = None
    else:
        plot_data["time_column"] = int(time_column_select.value)


def max_cols_callback(max_cols_select, plot_data):
    plot_data["max_cols"] = int(max_cols_select.value)


def col_labels_callback(col_labels_text, plot_data):
    if plot_data["delimiter"] == "whitespace":
        col_labels = col_labels_text.value.split()
    else:
        col_labels = col_labels_text.value.split(plot_data["delimiter"])

    if len(col_labels) > plot_data["max_cols"]:
        col_labels = col_labels[: plot_data["max_cols"]]
    elif len(col_labels) < plot_data["max_cols"]:
        col_labels += [
            str(col) for col in range(len(col_labels), plot_data["max_cols"])
        ]

    plot_data["col_labels"] = col_labels


def time_units_callback(time_units_select, time_column_select, p, plot_data):
    adjust_time_axis_label(time_column_select, time_units_select, p)

    plot_data["time_units"] = time_units_select.value


def delimiter_select_callback(delimiter_select, plot_data):
    if delimiter_select.value == "comma":
        plot_data["delimiter"] = ","
    elif delimiter_select.value == "space":
        plot_data["delimiter"] = " "
    elif delimiter_select.value == "tab":
        plot_data["delimiter"] = "\t"
    elif delimiter_select.value == "whitespace":
        plot_data["delimiter"] = "whitespace"
    elif delimiter_select.value == "vertical line":
        plot_data["delimiter"] = "|"
    elif delimiter_select.value == "semicolon":
        plot_data["delimiter"] = ";"
    elif delimiter_select.value == "asterisk":
        plot_data["delimiter"] = "*"
    elif delimiter_select.value == "slash":
        plot_data["delimiter"] = "/"


def input_send_callback(input_window, ascii_bytes, ser):
    """Send input to serial device."""
    if ser is not None and ser.is_open and input_window.value != "":
        message_ok = True
        if ascii_bytes.active == 1:
            try:
                # Input as bytes
                message = bytes([int(input_window.value)])
            except:
                input_window.value = "ERROR: Inputted bytes must be integers."
                message_ok = False
        else:
            try:
                message = input_window.value.encode("ascii")
            except:
                input_window.value = "ERROR: Cannot encode input as ASCII."
                message_ok = False

        if message_ok:
            ser.write(message)


def plot_save_callback(plot_save_button, plot_save_window):
    plot_save_button.visible = False
    plot_save_window.visible = True


def plot_write_callback(
    plot_file_input, plot_write, plot_save_window, plot_save_button, plot_data
):
    plot_save_button.visible = True
    plot_save_window.visible = False


def shutdown_callback(shutdown_button, confirm_shutdown_button, cancel_shutdown_button):
    shutdown_button.disabled = True
    shutdown_button.visible = False
    confirm_shutdown_button.visible = True
    cancel_shutdown_button.visible = True
    confirm_shutdown_button.disabled = False
    cancel_shutdown_button.disabled = False


def cancel_shutdown_callback(
    shutdown_button, confirm_shutdown_button, cancel_shutdown_button
):
    shutdown_button.disabled = False
    shutdown_button.visible = True
    confirm_shutdown_button.visible = False
    cancel_shutdown_button.visible = False
    confirm_shutdown_button.disabled = True
    cancel_shutdown_button.disabled = True


def confirm_shutdown_callback(ctrls, serial_dict):
    for widget in ctrls:
        ctrls[widget].disabled = True

    try:
        serial_dict["daq_task"].cancel()
    except:
        pass

    try:
        serial_dict["port_search_task"].cancel()
    except:
        pass

    # Close the connection if open
    if serial_dict["ser"] is not None:
        try:
            serial_dict["ser"].close()
            serial_dict["ser"] = None
        except:
            pass

    serial_dict["port_status"] = "disconnected"
    port_status_callback(ctrls["port_status"], serial_dict)

    serial_dict["kill_app"] = True
