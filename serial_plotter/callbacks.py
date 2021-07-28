import serial

from . import comms


def port_select_callback(port_select, serial_dict):
    """Store the selected port"""
    serial_dict["port"] = serial_dict["reverse_available_ports"][port_select.value]


def port_search_callback(port_select, serial_dict):
    """Update list of ports to be selected."""
    ports = serial.tools.list_ports.comports()

    options = [
        port_name.device
        + ("  " + port_name.manufacturer if port_name.manufacturer is not None else " ")
        for port_name in ports
    ]
    port_select.options = options

    # Dictionary of port names and name in port selector
    serial_dict["available_ports"] = {
        port_name.device: option_name for port_name, option_name in zip(ports, options)
    }

    # Reverse lookup for value in port selector to port name
    serial_dict["reverse_available_ports"] = {
        option_name: port_name.device for port_name, option_name in zip(ports, options)
    }


def baudrate_callback(baudrate_select, serial_dict):
    """Store the selected baudrate"""
    serial_dict["baudrate"] = baudrate_select.value


def port_connect_callback(port_status, serial_dict):
    """Connect to a port"""
    # try:
    if serial_dict["ser"] is not None:
        try:
            serial_dict["ser"].close()
        except:
            pass
    serial_dict["port_status"] = "establishing"
    port_status_callback(port_status, serial_dict)

    serial_dict["ser"] = serial.Serial(
        serial_dict["port"], baudrate=serial_dict["baudrate"]
    )
    comms.handshake_board(serial_dict["ser"])

    serial_dict["port_status"] = "connected"
    port_status_callback(port_status, serial_dict)
    # except:
    # serial_dict["ser"] = None
    # serial_dict["port_status"] = "failed"
    # port_status_callback(port_status, serial_dict)


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


def monitor_stream_callback(monitor_stream_toggle, plot_data):
    monitor_data["streaming"] = monitor_stream_toggle.active


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
