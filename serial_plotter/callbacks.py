import asyncio
import serial

from . import comms


def stream_update(
    plot, monitor, plot_data, monitor_data, source, phantom_source, rollover
):
    if monitor_data["streaming"]:
        monitor.text = (
            monitor.text[:-18]
            + "".join(monitor_data["data"][monitor_data["prev_array_length"] :])
            + "</pre></div></div>"
        )

        monitor_data["prev_array_length"] = len(monitor_data["data"])

    # TO ADD: Update plot


def port_search_callback(port_select, serial_dict):
    """Update available ports"""
    if port_select.options != list(serial_dict["reverse_available_ports"].keys()):
        port_select.options = list(serial_dict["reverse_available_ports"].keys())


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

    # try:
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

    # Disable port selectors now that we're connected
    port_connect.disabled = True
    port_select.disabled = True
    baudrate_select.disabled = True

    # Enable disconnecting
    port_disconnect.disabled = False

    #  Update status
    serial_dict["port_status"] = "connected"
    port_status_callback(port_status, serial_dict)

    # except:
    # serial_dict["ser"] = None
    # serial_dict["port_status"] = "failed"
    # port_status_callback(port_status, serial_dict)
    # try:
    #     serial_dict["daq_task"].cancel()


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
        port_status.text = f'<p><b>port status:</b> <font style="color: tomato;">unable to connect to {serial_dict["port"]}.</font></p>'


def plot_stream_callback(stream_toggle, plot_data):
    plot_data["streaming"] = stream_toggle.active


def monitor_stream_callback(monitor_stream_toggle, monitor_data):
    monitor_data["streaming"] = monitor_stream_toggle.active


def monitor_clear_callback(monitor_clear_toggle, monitor, monitor_data):
    monitor_data["data"] = ""
    monitor.text = monitor_data["base_text"]


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
