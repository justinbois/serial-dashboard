import asyncio
import copy
import os

import serial
import numpy as np
import pandas as pd

import bokeh.models

from . import comms
from . import parsers

# Color palette is from colorcet
_colors = [
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


def _update_legend(plotter):
    """Updates entries shown in legend"""
    active_col_labels = [
        x for i, x in enumerate(plotter.col_labels) if i != plotter.time_column
    ]

    if plotter.lines_visible and plotter.dots_visible:
        plotter.legend.items = [
            bokeh.models.LegendItem(label=col_label, renderers=[line, dot], index=col)
            for col, (col_label, line, dot) in enumerate(
                zip(active_col_labels, plotter.lines, plotter.dots)
            )
        ]
    elif plotter.lines_visible:
        plotter.legend.items = [
            bokeh.models.LegendItem(label=col_label, renderers=[line], index=col)
            for col, (col_label, line) in enumerate(
                zip(active_col_labels, plotter.lines)
            )
        ]
    elif plotter.dots_visible:
        plotter.legend.items = [
            bokeh.models.LegendItem(label=col_label, renderers=[dot], index=col)
            for col, (col_label, dot) in enumerate(zip(active_col_labels, plotter.dots))
        ]


def _glyph_visibility(plotter):
    """Updates visibility of glyphs"""
    for i, _ in enumerate(plotter.dots):
        plotter.dots[i].visible = plotter.dots_visible
        plotter.lines[i].visible = plotter.lines_visible


def _populate_glyphs(plotter, colors=_colors):
    # Define the data sources
    plotter.sources = [
        bokeh.models.ColumnDataSource(data=dict(t=[], y=[]))
        for _ in range(plotter.max_cols)
    ]

    # Lines
    plotter.lines = [
        plotter.plot.line(source=source, x="t", y="y", color=color)
        for color, source in zip(colors[: plotter.max_cols], plotter.sources)
    ]

    # Dots
    plotter.dots = [
        plotter.plot.scatter(source=source, x="t", y="y", color=color, size=3)
        for color, source in zip(colors[: plotter.max_cols], plotter.sources)
    ]

    # Set visibility
    _glyph_visibility(plotter)

    # Make a legend
    _update_legend(plotter)

    # Make legend visible
    plotter.plot.legend.visible = True


def _adjust_time_axis_label(plotter, monitor, controls, serial_connection):
    plotter.plot.xaxis.axis_label = parsers._xaxis_label(
        plotter.time_column, plotter.time_units
    )


def stream_update(plotter, monitor, controls, serial_connection):
    if monitor.streaming:
        monitor.monitor.text = (
            monitor.monitor.text[:-18]
            + "".join(monitor.data[monitor.prev_data_length :])
            + "</pre></div></div>"
        )

        monitor.prev_data_length = len(monitor.data)

    # Update plot by streaming in data
    if plotter.streaming:
        ty_dicts = parsers.data_to_dicts(
            plotter.data[plotter.prev_data_length :],
            plotter.max_cols,
            plotter.time_column,
            plotter.time_units,
            plotter.prev_data_length,
        )

        for i, ty_dict in enumerate(ty_dicts):
            plotter.sources[i].stream(ty_dict, plotter.rollover)

        # Adjust new phantom data point if new data arrived
        if len(plotter.sources) > 0 and len(plotter.sources[0].data["t"]) > 0:
            plotter.phantom_source.data = dict(
                t=[plotter.sources[0].data["t"][-1]],
                y=[plotter.sources[0].data["y"][-1]],
            )

        # Reset the array length
        plotter.prev_data_length = len(plotter.data)


def port_search_callback(plotter, monitor, controls, serial_connection):
    """Update available ports"""
    if controls.port.options != list(serial_connection.reverse_available_ports.keys()):
        controls.port.options = list(serial_connection.reverse_available_ports.keys())

        # Set the port to the first option if not already set
        if controls.port.value is None or controls.port.value == "":
            controls.port.value = controls.port.options[0]


def port_select_callback(plotter, monitor, controls, serial_connection):
    """Store the selected port"""
    serial_connection.port = serial_connection.reverse_available_ports[
        controls.port.value
    ]


def baudrate_callback(plotter, monitor, controls, serial_connection):
    """Store the selected baudrate"""
    serial_connection.baudrate = controls.baudrate.value


def port_connect_callback(plotter, monitor, controls, serial_connection):
    """Connect to a port"""
    # First shut down port searching
    try:
        serial_connection.port_search_task.cancel()
    except:
        pass
    serial_connection.port_search_task = None

    # Establish connection
    try:
        serial_connection.connect(
            serial_connection.port, allow_disconnect=True, handshake=True
        )

        # Start DAQ
        serial_connection.daq_task = asyncio.create_task(
            comms.daq_stream(
                plotter,
                monitor,
                serial_connection,
                n_reads_per_chunk=1,
                reader=comms.read_all,
            )
        )

        # Set up ColumnDataSources and populate glyphs for the plot
        _populate_glyphs(plotter)

        # Disable port selectors now that we're connected
        controls.port_connect.disabled = True
        controls.port.disabled = True
        controls.baudrate.disabled = True

        # Disable choice of mximum columns in input
        controls.max_cols.disabled = True

        # Enable disconnecting
        controls.port_disconnect.disabled = False

        # Enable sending data
        controls.input_send.disabled = False

        #  Update status
        port_status_callback(plotter, monitor, controls, serial_connection)
    except:
        serial_connection.port_status = "failed"
        serial_connection.ser = None
        port_status_callback(plotter, monitor, controls, serial_connection)
        try:
            serial_connection.daq_task.cancel()
        except:
            pass


def port_disconnect_callback(plotter, monitor, controls, serial_connection):
    """Disconnect serial device."""
    # Shut down DAQ task
    serial_connection.daq_task.cancel()
    serial_connection.daq_task = None

    # Close connection
    serial_connection.ser.close()

    # Re-enable buttons
    controls.port_connect.disabled = False
    controls.port.disabled = False
    controls.baudrate.disabled = False

    # We are going to keep max_cols locked in after first connect, so comment this out
    # controls.max_cols.disabled = False

    # Disable disconnecting
    controls.port_disconnect.disabled = True
    controls.input_send.disabled = True

    # Start port sniffer
    serial_connection.port_search_task = asyncio.create_task(
        comms.port_search(serial_connection)
    )

    # Update port status
    serial_connection.port_status = "disconnected"
    port_status_callback(plotter, monitor, controls, serial_connection)


def port_status_callback(plotter, monitor, controls, serial_connection):
    """Update port status text"""
    if serial_connection.port_status == "disconnected":
        controls.port_status.text = "<p><b>port status:</b> disconnected</p>"
    elif serial_connection.port_status == "establishing":
        controls.port_status.text = f"<p><b>port status:</b> establishing connection to {serial_connection.port}...</p>"
    elif serial_connection.port_status == "connected":
        controls.port_status.text = (
            f"<p><b>port status:</b> connected to {serial_connection.port}.</p>"
        )
    elif serial_connection.port_status == "failed":
        pass
        controls.port_status.text = f'<p><b>port status:</b> <font style="color: tomato;">unable to connect to {serial_connection.port}.</font></p>'


def plot_stream_callback(plotter, monitor, controls, serial_connection):
    plotter.streaming = controls.plot_stream.active


def plot_clear_callback(plotter, monitor, controls, serial_connection):
    # Blank the data set
    plotter.data = []

    # Reset all data sources
    for i in range(len(plotter.sources)):
        plotter.sources[i].data = dict(t=[], y=[])

    # Clear any remaining shrapnel from stale plots
    for renderer in plotter.plot.renderers:
        renderer.data_source.data = dict(t=[], y=[])

    # Reset the phantom data
    plotter.phantom_source.data = dict(phantom_t=[0], phantom_y=[0])


def monitor_stream_callback(plotter, monitor, controls, serial_connection):
    monitor.streaming = controls.monitor_stream.active


def monitor_clear_callback(plotter, monitor, controls, serial_connection):
    monitor.data = ""
    monitor.monitor.text = monitor.base_text


def time_column_callback(plotter, monitor, controls, serial_connection):
    if controls.time_column.value == "none":
        plotter.time_column = "none"
    else:
        plotter.time_column = int(controls.time_column.value)

    _adjust_time_axis_label(plotter, monitor, controls, serial_connection)

    # Update legend if possible (i.e., if _populate_glyphs() has already been called)
    try:
        _update_legend(plotter)
    except:
        pass


def max_cols_callback(plotter, monitor, controls, serial_connection):
    plotter.max_cols = int(controls.max_cols.value)

    if len(plotter.col_labels) > plotter.max_cols:
        plotter.col_labels = plotter.col_labels[: plotter.max_cols]
    elif len(plotter.col_labels) < plotter.max_cols:
        plotter.col_labels += [
            str(col) for col in range(len(plotter.col_labels), plotter.max_cols)
        ]


def col_labels_callback(plotter, monitor, controls, serial_connection):
    col_labels = parsers._column_labels_str_to_list(
        controls.col_labels.value, plotter.delimiter, plotter.max_cols
    )

    # Update stored labels
    plotter.col_labels = col_labels

    # Update legend if possible (i.e., if _populate_glyphs() has already been called)
    try:
        _update_legend(plotter)
    except:
        pass


def rollover_callback(plotter, monitor, controls, serial_connection):
    plotter.rollover = int(controls.rollover.value)


def glyph_callback(plotter, monitor, controls, serial_connection):
    plotter.lines_visible = True if controls.glyph.active in [0, 2] else False
    plotter.dots_visible = True if controls.glyph.active in [1, 2] else False

    # Update visibility of glyphs if _populate_glyphs() has already been called)
    try:
        _glyph_visibility(plotter)
    except:
        pass

    # Update legend if possible (i.e., if _populate_glyphs() has already been called)
    try:
        _update_legend(plotter)
    except:
        pass


def time_units_callback(plotter, monitor, controls, serial_connection):
    plotter.time_units = controls.time_units.value
    _adjust_time_axis_label(plotter, monitor, controls, serial_connection)


def delimiter_select_callback(plotter, monitor, controls, serial_connection):
    plotter.delimiter = parsers.delimiter_convert(controls.delimiter.value)


def input_send_callback(plotter, monitor, controls, serial_connection):
    """Send input to serial device."""
    if (
        serial_connection.ser is not None
        and serial_connection.ser.is_open
        and controls.input_window.value != ""
    ):
        message_ok = True
        if controls.ascii_bytes.active == 1:
            try:
                # Input as bytes
                message = bytes([int(controls.input_window.value)])
            except:
                controls.input_window.value = "ERROR: Inputted bytes must be integers."
                message_ok = False
        else:
            try:
                message = controls.input_window.value.encode("ascii")
            except:
                controls.input_window.value = "ERROR: Cannot encode input as ASCII."
                message_ok = False

        if message_ok:
            serial_connection.ser.write(message)


def plot_save_callback(plotter, monitor, controls, serial_connection):
    controls.plot_save.visible = False
    controls.plot_file_input.visible = True
    controls.plot_write.visible = True


def plot_write_callback(plotter, monitor, controls, serial_connectionr):
    controls.plot_save.visible = True
    controls.plot_file_input.visible = False
    controls.plot_write.visible = False
    controls.plot_save_notice.text = f'<p style="font-size: 8pt;">Data last saved to {controls.plot_file_input.value}.</p>'

    fname = controls.plot_file_input.value.rstrip()

    if os.path.isfile(fname):
        notice_text = f'<p style="font-size: 8pt; color: tomato;">File {fname} exists. Refused to overwrite.</p>'
    else:
        try:
            # Fill out data set with NaNs
            data, ncols = parsers.fill_nans(copy.copy(plotter.data), 0)

            if len(data) == 0 or ncols == 0:
                notice_text = f'<p style="font-size: 8pt; color: tomato;">No plotter data available to write.</p>'
            else:
                # Appropriately pad data set if too many/few columns
                if ncols > len(plotter.col_labels):
                    columns = plotter.col_labels + [
                        i for i in range(len(plotter.col_labels), ncols)
                    ]
                    df = pd.DataFrame(data=data, columns=columns)
                else:
                    if ncols < len(plotter.col_labels):
                        data = parsers.backfill_nans(data, len(plotter.col_labels))
                    df = pd.DataFrame(data=data, columns=plotter.col_labels)

                df.to_csv(fname, index=False)

                notice_text = (
                    f'<p style="font-size: 8pt;">Data last saved to {fname}.</p>'
                )
        except:
            notice_text = f'<p style="font-size: 8pt; color: tomato;">Failed to write to file {fname}.</p>'

    controls.plot_save_notice.text = notice_text


def monitor_save_callback(plotter, monitor, controls, serial_connection):
    controls.monitor_save.visible = False
    controls.monitor_file_input.visible = True
    controls.monitor_write.visible = True


def monitor_write_callback(plotter, monitor, controls, serial_connection):
    controls.monitor_save.visible = True
    controls.monitor_file_input.visible = False
    controls.monitor_write.visible = False

    fname = controls.monitor_file_input.value.rstrip()

    if os.path.isfile(fname):
        notice_text = f'<p style="font-size: 8pt; color: tomato;">File {fname} exists. Refused to overwrite.</p>'
    else:
        try:
            with open(fname, "w") as f:
                f.write("".join(monitor.data))

            notice_text = f'<p style="font-size: 8pt;">Data last saved to {fname}.</p>'

        except:
            notice_text = f'<p style="font-size: 8pt; color: tomato;">Failed to write to file {fname}.</p>'

    controls.monitor_save_notice.text = notice_text


def shutdown_callback(plotter, monitor, controls, serial_connection):
    controls.shutdown.disabled = True
    controls.shutdown.visible = False
    controls.confirm_shutdown.visible = True
    controls.cancel_shutdown.visible = True
    controls.confirm_shutdown.disabled = False
    controls.cancel_shutdown.disabled = False


def cancel_shutdown_callback(plotter, monitor, controls, serial_connection):
    controls.shutdown.disabled = False
    controls.shutdown.visible = True
    controls.confirm_shutdown.visible = False
    controls.cancel_shutdown.visible = False
    controls.confirm_shutdown.disabled = True
    controls.cancel_shutdown.disabled = True


def confirm_shutdown_callback(plotter, monitor, controls, serial_connection):
    for widget_name, widget in controls.__dict__.items():
        try:
            widget.disabled = True
        except:
            pass

    try:
        serial_connection.daq_task.cancel()
    except:
        pass

    try:
        serial_connection.port_search_task.cancel()
    except:
        pass

    # Close the connection if open
    if serial_connection.ser is not None:
        try:
            serial_connection.ser.close()
            serial_connection.ser = None
        except:
            pass

    serial_connection.port_status = "disconnected"
    port_status_callback(plotter, monitor, controls, serial_connection)

    serial_connection.kill_app = True
