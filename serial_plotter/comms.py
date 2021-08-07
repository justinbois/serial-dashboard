import asyncio
import serial
import time

import numpy as np

from . import callbacks


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


def parse_read(read, sep=",", n_reads=0):
    """Parse a read with time, voltage data

    Parameters
    ----------
    read : byte string
        Byte string with comma delimited time/voltage
        measurements.
    sep : str, default ','
        Character separating columns of written data.
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
    data = []

    # Read in lines of raw data
    raw_list = read.decode().split("\n")

    for raw in raw_list[:-1]:
        try:
            if sep == "whitespace":
                read_data = raw.split()
            else:
                read_data = raw.split(sep)

            new_data = []
            for datum in read_data:
                datum = datum.strip()
                if datum.isdecimal():
                    new_data.append(int(datum))
                else:
                    try:
                        new_data.append(float(datum))
                    except:
                        new_data.append(np.nan)
            data.append(new_data)
            n_reads += 1
        except:
            pass

    if len(raw_list[-1]) == 0:
        return data, n_reads, b""
    else:
        return data, n_reads, raw_list[-1].encode()


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


def backfill_nans(x, ncols):
    """Given a 2D Numpy array, right-append an array of NaNs such that
    there are ncols in the resulting array.

    Parameters
    ----------
    x : 2D Numpy array
        Array to be NaN filled

    Returns
    -------
    x_out : 2D Numpy array
        A 2D Numpy array, right-padded with NaNs.
    """
    ncols_x = x.shape[1]

    if ncols_x >= ncols:
        return x

    nan_array = np.empty((len(x), ncols - ncols_x))
    nan_array.fill(np.nan)

    return np.concatenate((x, nan_array), axis=1)


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
            # Parse it, passing if it is gibberish or otherwise corrupted
            try:
                data, n_reads, read_buffer[0] = parse_read(
                    raw, sep=plot_data["delimiter"]
                )

                # Proceed if we actually read in data
                if len(data) > 0:
                    # Make sure all read in data has the same number of columns
                    data, ncols = fill_nans(data, plot_data["ncols"])

                    # If this is our first data, add them into plot_data
                    if len(plot_data["data"]) == 0:
                        plot_data["data"] = data.copy()
                        plot_data["ncols"] = ncols
                    else:
                        # If the new data added columns, backfill previous data with NaNs
                        if ncols > plot_data["ncols"]:
                            plot_data["data"] = backfill_nans(plot_data["data"], ncols)
                            plot_data["ncols"] = ncols

                            # Alert that the ColumnDataSource needs to be refreshed
                            plot_data["source_needs_refresh"] = True

                        # If the new data has less columns, fill in new data with NaNs
                        elif ncols < plot_data["ncols"]:
                            data = backfill_nans(data, plot_data["ncols"])

                        # Update data
                        plot_data["data"] = np.concatenate(
                            (plot_data["data"], data), axis=0
                        )
            except:
                pass

        if monitor_data["streaming"]:
            monitor_data["data"] += raw.decode()

        # Sleep 80% of the time before we need to start reading chunks
        await asyncio.sleep(0.8 * n_reads_per_chunk * delay / 1000)


async def port_search_async(port_select, serial_dict):
    """Search for ports"""
    while True:
        ports = serial.tools.list_ports.comports()

        if ports != serial_dict["ports"]:
            serial_dict["ports"] = [port for port in ports]

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
            serial_dict["available_ports"] = {
                port_name.device: option_name
                for port_name, option_name in zip(ports, options)
            }

            # Reverse lookup for value in port selector to port name
            serial_dict["reverse_available_ports"] = {
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
