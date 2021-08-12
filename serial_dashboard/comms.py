import asyncio
import serial
import time

import numpy as np

from . import callbacks
from . import parsers


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


async def daq_stream_async(
    plotter, monitor, serial_connection, delay=20, n_reads_per_chunk=1, reader=read_all
):
    """Obtain streaming data"""
    # Receive data
    read_buffer = [b""]
    while True:
        # Read in chunk of data
        raw = reader(
            serial_connection.ser, read_buffer=read_buffer[0], n_reads=n_reads_per_chunk
        )

        if plotter.streaming:
            # Parse it, passing if it is gibberish or otherwise corrupted
            try:
                data, n_reads, read_buffer[0] = parsers.parse_read(
                    raw, sep=plotter.delimiter
                )

                # Proceed if we actually read in data
                if len(data) > 0:
                    # If this is our first data, add them into plot_data
                    if len(plotter.data) == 0:
                        plotter.data = data
                    else:
                        plotter.data += data
            except:
                pass

        if monitor.streaming:
            monitor.data += raw.decode()

        # Sleep 80% of the time before we need to start reading chunks
        await asyncio.sleep(0.8 * n_reads_per_chunk * delay / 1000)


async def port_search_async(serial_connection):
    """Search for ports"""
    while True:
        ports = serial.tools.list_ports.comports()

        if ports != serial_connection.ports:
            serial_connection.ports = [port for port in ports]

            options = [
                port_name.device
                + (
                    "  " + port_name.manufacturer
                    if port_name.manufacturer is not None
                    else ""
                )
                for port_name in ports
            ]

            # Dictionary of port names and name in port selector
            serial_connection.available_ports = {
                port_name.device: option_name
                for port_name, option_name in zip(ports, options)
            }

            # Reverse lookup for value in port selector to port name
            serial_connection.reverse_available_ports = {
                option_name: port_name.device
                for port_name, option_name in zip(ports, options)
            }

        # Sleep a second before searching again
        await asyncio.sleep(1)


def handshake_board(ser, sleep_time=1):
    """Connect to board by closing, then opening connection."""
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

    # Reset the timeout
    ser.timeout = timeout
