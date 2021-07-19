import asyncio
import re
import requests
import sys
import time

import numpy as np
import pandas as pd

import serial
import serial.tools.list_ports

import bokeh.plotting
import bokeh.io
import bokeh.layouts
import bokeh.driving

from .boards import vid_pid_boards


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


def handshake_board(
    ser, sleep_time=1, print_handshake_message=False, handshake_code=0
):
    """Make sure connection is established by sending and receiving
    bytes."""
    # Close and reopen
    ser.close()
    ser.open()

    # Chill out while everything gets set
    time.sleep(sleep_time)

    # Set a long timeout to complete handshake
    timeout = ser.timeout
    ser.timeout = 2

    # Read and discard everything that may be in the input buffer
    _ = ser.read_all()

    # Send request to board
    ser.write(bytes([handshake_code]))

    # Read in what board sent
    handshake_message = ser.read_until()

    # Send and receive request again
    ser.write(bytes([handshake_code]))
    handshake_message = ser.read_until()

    # Print the handshake message, if desired
    if print_handshake_message:
        print("Handshake message: " + handshake_message.decode())

    # Reset the timeout
    ser.timeout = timeout


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


def read_all_newlines(ser, read_buffer=b"", n_reads=4):
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


def parse_read(read, sep=" ", time_column=None, n_reads=0):
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
            data = raw.split(sep)
            if time_column is None:
                time_ms.append(n_reads)
            else:
                time_ms.append(int(data.pop(time_column)))
            n_reads += 1
        except:
            pass

    if len(raw_list) == 0:
        return time_ms, data, n_reads, b""
    else:
        return time_ms, data, n_reads, raw_list[-1].encode()


def plot():
    """Build a plot of data vs time data"""
    # Set up plot area
    p = bokeh.plotting.figure(
        frame_width=500,
        frame_height=175,
        x_axis_label="time (s)",
        y_axis_label="voltage (V)",
        y_range=[-5, 1029],
        toolbar_location="above",
    )

    # No range padding on x: signal spans whole plot
    p.x_range.range_padding = 0

    # We'll sue whitesmoke backgrounds
    p.border_fill_color = "whitesmoke"

    # Put a phantom circle so axis labels show before data arrive
    phantom_source = bokeh.models.ColumnDataSource(data=dict(phantom_t=[0], phantom_data=[0]))
    p.circle(source=phantom_source, x="phantom_t", y="phantom_data", visible=False)

    return p, source, phantom_source


def populate_glyphs(data)
    # Define the data source
    data_dict = {'data' + str(i): [] for i in range(n_data)}
    data_dict["t"] = []
    source = bokeh.models.ColumnDataSource(data=data_dict)

    # Populate glyphs
    for i in range(n_data):
        p.line(source=source, x="t", y="data" + str(i))



def controls(mode):
    acquire = bokeh.models.Toggle(label="stream", button_type="success", width=100)
    save_notice = bokeh.models.Div(
        text="<p>No streaming data saved.</p>", width=165
    )

    save = bokeh.models.Button(label="save", button_type="primary", width=100)
    reset = bokeh.models.Button(label="reset", button_type="warning", width=100)
    file_input = bokeh.models.TextInput(
        title="file name", value=f"{mode}.csv", width=165
    )

    return dict(
        acquire=acquire,
        reset=reset,
        save=save,
        file_input=file_input,
        save_notice=save_notice,
    )


def layout(p, ctrls):
    buttons = bokeh.layouts.row(
        bokeh.models.Spacer(width=30),
        ctrls["acquire"],
        bokeh.models.Spacer(width=295),
        ctrls["reset"],
    )
    left = bokeh.layouts.column(p, buttons, spacing=15)
    right = bokeh.layouts.column(
        bokeh.models.Spacer(height=50),
        ctrls["file_input"],
        ctrls["save"],
        ctrls["save_notice"],
    )
    return bokeh.layouts.row(
        left, right, spacing=30, margin=(30, 30, 30, 30), background="whitesmoke",
    )


def stream_callback(ser, stream_data, new):
    if new:
        stream_data["mode"] = "stream"
    else:
        stream_data["mode"] = "ignore"

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


def data_dict()

async def daq_stream_async(
    arduino,
    data,
    delay=20,
    n_trash_reads=5,
    n_reads_per_chunk=4,
    reader=read_all_newlines,
):
    """Obtain streaming data"""
    # Specify delay
    arduino.write(bytes([READ_DAQ_DELAY]) + (str(delay) + "x").encode())

    # Current streaming state
    stream_on = False

    # Receive data
    read_buffer = [b""]
    while True:
        if data["mode"] == "stream":
            # Turn on the stream if need be
            if not stream_on:
                arduino.write(bytes([STREAM]))

                # Read and throw out first few reads
                i = 0
                while i < n_trash_reads:
                    _ = arduino.read_until()
                    i += 1

                stream_on = True

            # Read in chunk of data
            raw = reader(arduino, read_buffer=read_buffer[0], n_reads=n_reads_per_chunk)

            # Parse it, passing if it is gibberish
            try:
                t, V, read_buffer[0] = parse_read(raw)

                # Update data dictionary
                data["t"] += t
                data["V"] += V
            except:
                pass
        else:
            # Make sure stream is off
            stream_on = False

        # Sleep 80% of the time before we need to start reading chunks
        await asyncio.sleep(0.8 * n_reads_per_chunk * delay / 1000)

