import copy
import numpy as np


def parse_read(read, sep=",", n_reads=0):
    """Parse a read with incoming delimited data.

    Parameters
    ----------
    read : byte string
        Byte string with comma delimited time/voltage
        measurements.
    sep : str, default ','
        Delimiting character separating columns of written data.
    n_reads : int, default 0
        The number of reads that have previously been read in.

    Returns
    -------
    data : list of ints
        Parsed data.
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
    - `x` is modified in place. Do not use this function if you want `x` back.
    - There is no type-checking on `x`. It must be a list of lists.
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
        Array to be NaN filled.
    ncols : int
        Number of columns in resulting array.

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


def data_to_dicts(data, max_cols, time_col, time_units, starting_time_ind):
    """Take in data as a list of lists and converts to a list of
    dictionaries that can be used to stream into the ColumnDataSources.

    Parameters
    ----------
    data : list of lists
        Data to be converted into a dictionary.
    max_cols : int
        Maximum number of columns present in data set. This is usually
        the maximum length of a one of the lists in `data`. If any of
        the lists are longer than `max_cols`, the data in the list is
        truncated.
    time_col : int or "none"
        Which column contains time data.
    time_units : str
        Units of time. If "µs", the time column is divided by a million.
        If "ms", the time column is divided by a thousand.
    starting_time_ind : int
        Only active if `time_col == "none"`. The time column is indices
        in this case, and they start with `starting_time_ind`.

    Returns
    -------
    output : list of dicts
        A list of dicts, each with keys "t" and "y", representing the
        time and y-data to be updated in a plot.
    """
    data, ncols = fill_nans(copy.copy(data), 0)
    if len(data) == 0 or ncols == 0:
        return [dict(t=[], y=[]) for _ in range(ncols)]

    ts = []
    ys = []
    if time_col == "none":
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


def _delimiter_convert(delimiter):
    if delimiter == "comma":
        return ","
    elif delimiter == "space":
        return " "
    elif delimiter == "tab":
        return "\t"
    elif delimiter == "whitespace":
        return "whitespace"
    elif delimiter == "vertical line":
        return "|"
    elif delimiter == "semicolon":
        return ";"
    elif delimiter == "asterisk":
        return "*"
    elif delimiter == "slash":
        return "/"


def _column_labels_str_to_list(col_labels, delimiter, max_cols):
    if len(col_labels) == 0:
        return [str(col) for col in range(max_cols)]

    if delimiter == "whitespace":
        col_labels = col_labels.split()
    else:
        col_labels = col_labels.split(delimiter)

    if len(col_labels) > max_cols:
        col_labels = col_labels[:max_cols]
    elif len(col_labels) < max_cols:
        col_labels += [str(col) for col in range(len(col_labels), max_cols)]

    return col_labels


def _xaxis_label(time_column, time_units):
    if time_column == "none":
        label = "sample number"
    elif time_units in ("µs", "ms", "s"):
        label = "time (s)"
    elif time_units == "none":
        label = "time"
    else:
        label = f"time ({time_units})"

    return label
