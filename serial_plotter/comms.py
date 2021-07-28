import time


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
