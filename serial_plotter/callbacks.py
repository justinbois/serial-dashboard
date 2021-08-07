import asyncio
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
    "#3a0182",
    "#004201",
    "#0fffa8",
    "#5d003f",
    "#bcbcff",
    "#d8afa1",
    "#b80080",
    "#004d52",
    "#6b6400",
    "#7c0100",
    "#6026ff",
    "#ffff9a",
    "#564964",
    "#8cb893",
    "#93fbff",
    "#018267",
    "#90ff00",
    "#8200a0",
    "#ac8944",
    "#5b3400",
    "#ffbff2",
    "#ff6e75",
    "#798cff",
    "#dd00ff",
    "#505646",
    "#004489",
    "#ffbf60",
    "#ff018c",
    "#bdc8cf",
    "#af97b5",
    "#b65600",
    "#017000",
    "#cd87ff",
    "#1cd646",
    "#bfebc3",
    "#7997b5",
    "#a56089",
    "#6e8956",
    "#bc7c75",
    "#8a2844",
    "#00acff",
    "#8ed4ff",
    "#4b6d77",
    "#00d4b1",
    "#9300f2",
    "#8a9500",
    "#5d5b9e",
    "#fddfba",
    "#00939e",
    "#ffdb00",
    "#00aa79",
    "#520067",
    "#000091",
    "#0a5d3d",
    "#a5e275",
    "#623b41",
    "#c6c689",
    "#ff9eb5",
    "#cd4f6b",
    "#ff07d6",
    "#8a3a05",
    "#7e3d70",
    "#ff4901",
    "#602ba5",
    "#1c00ff",
    "#e6dfff",
    "#aa3baf",
    "#d89c00",
    "#a3a39e",
    "#3f69ff",
    "#46490c",
    "#7b6985",
    "#6b978c",
    "#ff9a75",
    "#835bff",
    "#7c6b46",
    "#80b654",
    "#bc0049",
    "#fd93ff",
    "#5d0018",
    "#89d1d1",
    "#9c8cd3",
    "#da6d42",
    "#8a5700",
    "#3b5069",
    "#4b6b3b",
    "#edcfd8",
    "#cfedff",
    "#aa1500",
    "#dfff4f",
    "#ff2a56",
    "#d1499e",
    "#707cb8",
    "#598000",
    "#00e4fd",
    "#774b95",
    "#67d48c",
    "#3d3a72",
    "#ac413f",
    "#d6a166",
    "#c169cd",
    "#69595d",
    "#87aced",
    "#a0a569",
    "#d1aae6",
    "#870062",
    "#00fddb",
    "#672818",
    "#b342ff",
    "#0e59c4",
    "#168742",
    "#90d300",
    "#cd7900",
    "#f959ff",
    "#5b7466",
    "#8eaeb3",
    "#9c7c8c",
    "#4600c6",
    "#6b4d2d",
    "#a56d46",
    "#9e8972",
    "#a8afca",
    "#cd8ca7",
    "#00fd64",
    "#917900",
    "#ff62a1",
    "#f4ffd8",
    "#018cf0",
    "#13aca0",
    "#5b2d59",
    "#89859e",
    "#cfccba",
    "#d4afc4",
    "#dbdd6d",
    "#cffff4",
    "#006485",
    "#006962",
    "#a84167",
    "#2d97c4",
    "#a874ff",
    "#26ba5d",
    "#57b600",
    "#caffa7",
    "#a379aa",
    "#ffbc93",
    "#89e2c1",
    "#0fc8ff",
    "#d400c4",
    "#626d89",
    "#69858e",
    "#4b4d52",
    "#aa6067",
    "#79b5d4",
    "#2b5916",
    "#9a0024",
    "#bdd1f2",
    "#896e67",
    "#69a56b",
    "#855467",
    "#aecdba",
    "#87997e",
    "#cadb00",
    "#9a0390",
    "#ebbc1a",
    "#eb9cd1",
    "#70006e",
    "#b1a131",
    "#ca6b93",
    "#4146a3",
    "#e48c89",
    "#d44400",
    "#c68aca",
    "#b69597",
    "#d41f75",
    "#724bcc",
    "#674d00",
    "#672138",
    "#38564f",
    "#6ebaaa",
    "#853a31",
    "#a5d397",
    "#b8af8e",
    "#d8e4df",
    "#aa00df",
    "#cac1db",
    "#ffdf8c",
    "#e2524d",
    "#66696e",
    "#ff001c",
    "#522d72",
    "#4d906b",
    "#a86d11",
    "#ff9e26",
    "#5ea3af",
    "#c88556",
    "#915997",
    "#a3a1ff",
    "#fdbaba",
    "#242a87",
    "#dbe6a8",
    "#97f2a7",
    "#6793d6",
    "#ba5b3f",
    "#3a5d91",
    "#364f2f",
    "#267c95",
    "#89959a",
    "#cfb356",
    "#004664",
    "#5e5d2f",
    "#8e8e41",
    "#ac3f13",
    "#69953b",
    "#a13d85",
    "#bfb6ba",
    "#acc667",
    "#6469cf",
    "#91af00",
    "#2be2da",
    "#016e36",
    "#ff7952",
    "#42807e",
    "#4fe800",
    "#995428",
    "#5d0a00",
    "#a30057",
    "#0c8700",
    "#5982a7",
    "#ffebfb",
    "#4b6901",
    "#8775d4",
    "#e6c6ff",
    "#a5ffda",
    "#d86e77",
    "#df014b",
    "#69675b",
    "#776ba1",
    "#7e8067",
    "#594685",
    "#0000ca",
    "#7c002a",
    "#97ff72",
    "#b5e2e1",
    "#db52c8",
    "#777734",
    "#57bd8e",
]


def populate_glyphs(
    p, plot_dict, colors=colors,
):
    # Define the data sources
    plot_dict["sources"] = [
        bokeh.models.ColumnDataSource(data=dict(t=[], y=[]))
        for _ in range(plot_dict["max_cols"])
    ]

    # Lines
    plot_dict["lines"] = [
        p.line(source=source, x="t", y="y", color=color)
        for color, source in zip(colors[: plot_dict["max_cols"]], sources)
    ]
    plot_dict["dots"] = [
        p.circle(source=source, x="t", y="y", color=color, size=3)
        for color, source in zip(colors[: plot_dict["max_cols"]], sources)
    ]

    # Start with just lines visible
    for i, _ in enumerate(dots):
        dots[i].visible = False


def stream_update(plot, monitor, plot_data, monitor_data, rollover):
    if monitor_data["streaming"]:
        monitor.text = (
            monitor.text[:-18]
            + "".join(monitor_data["data"][monitor_data["prev_array_length"] :])
            + "</pre></div></div>"
        )

        monitor_data["prev_array_length"] = len(monitor_data["data"])

    # Update plot by streaming in data
    if plot_data["streaming"]:
        if plot_data["source_needs_refresh"]:
            # How many data points to include in ColumnDataSource
            n = min(len(plot_data["data"]), rollover)

            # Time points
            if (
                plot_data["time_column"] is None
                or plot_data["time_column"] >= plot_data["ncols"]
            ):
                t = np.arange(n)
            else:
                t = plot_data["source"].data["t"][-n:]

            # Construct dictionary for column data source
            data_dict = dict(t=t.copy())
            j = 0
            for i in range(plot_data["ncols"]):
                if i != plot_data["time_column"]:
                    data_dict[f"y{j}"] = plot_data["data"][-n:, j]
                    j += 1

            # Create column data source
            #            CAN'T DECONSTRUCT/CONSTRUCT CDS. JUST ADJUST DATA.
            plot_data["source"] = bokeh.models.ColumnDataSource(data=data_dict)

            # Establish non-time columns
            cols = [key for key in plot_data["source"].data if "y" in key]

            # Populate glyphs
            plot_data["lines"] = [
                plot.line(source=plot_data["source"], x="t", y=col, color=color)
                for col, color in zip(cols, colors[: len(cols)])
            ]
            plot_data["dots"] = [
                plot.circle(
                    source=plot_data["source"], x="t", y=col, color=color, size=3
                )
                for col, color in zip(cols, colors[: len(cols)])
            ]

            for i, _ in enumerate(plot_data["dots"]):
                plot_data["dots"][i].visible = False

            plot_data["source_needs_refresh"] = False

        # Create new time data
        if plot_data["data"].size > 0:
            if plot_data["time_column"] is None:
                t = (
                    plot_data["source"].data["t"][-1]
                    + 1
                    + np.arange(len(plot_data["data"]) - plot_data["prev_array_length"])
                )
            else:
                t = plot_data["data"][
                    plot_data["prev_array_length"] :, plot_data["time_column"]
                ]
                if plot_data["time_units"] == "µs":
                    t = t / 1e6
                elif plot_data["time_units"] == "ms":
                    t = t / 1000
        else:
            t = np.array([])

        new_data = dict(t=t)

        # New y-data
        j = 0
        for i in range(plot_data["ncols"]):
            if i != plot_data["time_column"]:
                new_data[f"y{j}"] = plot_data["data"][
                    plot_data["prev_array_length"] :, j
                ]
                j += 1

        print(new_data)

        # Add the new data to the source
        plot_data["source"].stream(new_data, rollover)

        # Adjust new phantom data point if new data arrived
        if len(new_data["t"] > 0):
            plot_data["phantom_source"].data = dict(
                t=[new_data["t"][-1]], y=[new_data["y1"][-1]]
            )

        # Reset the array length
        plot_data["prev_array_length"] = len(plot_data["data"])


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
    port_status,
    serial_dict,
    plot_data,
    monitor_data,
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

        # Set up ColumnDataSources for the plot
        serial_dict["sources"] = [
            bokeh.models.ColumnDataSource(dict(t=[], y=[]))
            for _ in range(plot_data["max_cols"])
        ]

        # Disable port selectors now that we're connected
        port_connect.disabled = True
        port_select.disabled = True
        baudrate_select.disabled = True

        # Enable disconnecting
        port_disconnect.disabled = False

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
    port_status,
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

    # Disable disconnecting
    port_disconnect.disabled = True

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
    plot_data["source"].data = {key: [] for key in plot_data["source"].data}
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


def time_units_callback(time_units_select, p, plot_data):
    adjust_time_axis_label(time_column_select, time_units_select, p)

    plot_data["time_units"] = time_units_select.value


def delimiter_select_callback(delimiter_select, plot_data):
    if delimiter_select["value"] == "comma":
        plot_data["delimiter"] = ","
    elif delimiter["value"] == "space":
        plot_data["delimiter"] = " "
    elif delimiter["value"] == "tab":
        plot_data["delimiter"] = "\t"
    elif delimiter["value"] == "whitespace":
        plot_data["delimiter"] = "whitespace"
    elif delimiter["value"] == "vertical line":
        plot_data["delimiter"] = "|"
    elif delimiter["value"] == "semicolon":
        plot_data["delimiter"] = ";"
    elif delimiter["value"] == "asterisk":
        plot_data["delimiter"] = "*"
    elif delimiter["value"] == "slash":
        plot_data["delimiter"] = "/"


def input_window_callback(input_window, ascii_bytes, ser):
    """Send input to serial device."""
    if ser is not None and ser.is_open:
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
