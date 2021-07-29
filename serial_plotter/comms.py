import asyncio
import serial
import time

from . import callbacks


def parse_read(read, sep=" ", time_column=None, time_units="ms", n_reads=0):
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
    time_units : str, default "ms"
        One of [None, 'µs', 'ms', 's', 'min', 'hr']. All times are
        converted to milliseconds, except for None, which is only
        allowed when time_column is None.
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
            read_data = raw.split(sep)
            data.append(
                [
                    int(datum) if datum.isdecimal() else float(datum)
                    for datum in read_data
                ]
            )
            if time_column is None:
                time_ms.append(n_reads)
            else:
                time_ms.append(time_in_ms(read_data.pop(time_column), time_units))
            n_reads += 1
        except:
            pass

    if len(raw_list) == 0:
        return time_ms, data, n_reads, b""
    else:
        return time_ms, data, n_reads, raw_list[-1].encode()


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
    ser, plot_data, monitor_data, delay=20, n_reads_per_chunk=1, reader=read_all,
):
    """Obtain streaming data"""
    # Receive data
    read_buffer = [b""]
    while True:
        # Read in chunk of data
        raw = reader(ser, read_buffer=read_buffer[0], n_reads=n_reads_per_chunk)

        if plot_data["streaming"]:
            # Parse it, passing if it is gibberish
            try:
                t, V, read_buffer[0] = parse_read(raw)

                # Update data dictionary
                data["t"] += t
                data["V"] += V
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
                    else " "
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
