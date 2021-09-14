import click
import serial_dashboard


def _check_baudrate_cli(baudrate):
    if baudrate not in serial_dashboard.allowed_baudrates:
        click.echo("  ERROR", err=True)
        click.echo(
            f"  Inputted baudrate {baudrate} is not allowed. Allowed baudrates (in units of baud = bits per second) are: ",
            err=True,
        )

        for br in serial_dashboard.allowed_baudrates:
            click.echo(f"    {br}", err=True)

        click.echo("")

        return False
    else:
        return True


def _check_maxcols_cli(maxcols):
    if maxcols < 1 or maxcols > serial_dashboard.max_max_cols:
        click.echo("  ERROR", err=True)
        click.echo(
            f"  Inputted maxcols {maxcols} is invalid. maxcols must be between 1 and {serial_dashboard.max_max_cols}.",
            err=True,
        )
        click.echo("")

        return False
    else:
        return True


def _check_delimiter_cli(delimiter):
    if delimiter not in serial_dashboard.allowed_delimiters:
        click.echo("  ERROR", err=True)
        click.echo(
            f'  Inputted delimiter "{delimiter}" is not allowed. Allowed delimiters are: ',
            err=True,
        )

        for dl in serial_dashboard.allowed_delimiters:
            click.echo(f"    {dl}", err=True)

        click.echo("")

        return False
    else:
        return True


def _check_timecolumn_cli(timecolumn, maxcols):
    if timecolumn == "none":
        return True

    try:
        timecolumn = int(timecolumn)
    except:
        click.echo("  ERROR", err=True)
        click.echo(
            f"  Inputted timecolumn {timecolumn} is invalid. timecolumn must be an integer.",
            err=True,
        )
        click.echo("")

        return False

    if timecolumn < 0 or timecolumn >= maxcols:
        click.echo("  ERROR", err=True)
        click.echo(
            f"  Inputted timecolumn {timecolumn} is invalid. Must have 0 ≤ timecolumn < maxcols. You have selected maxcols = {maxcols}.",
            err=True,
        )
        click.echo("")

        return False

    return True


def _check_timeunits_cli(timeunits):
    if timeunits not in serial_dashboard.allowed_timeunits:
        click.echo("  ERROR", err=True)
        click.echo(
            f'  Inputted timeunits "{timeunits}" is not allowed. Allowed time units are: ',
            err=True,
        )

        for tu in serial_dashboard.allowed_timeunits:
            click.echo(f"    {tu}", err=True)

        click.echo("")

        return False
    else:
        return True


def _check_rollover_cli(rollover):
    if rollover not in serial_dashboard.allowed_rollover:
        click.echo("  ERROR", err=True)
        click.echo(
            f'  Inputted rollover "{rollover}" is not allowed. Allowed rollover values are: ',
            err=True,
        )

        for ro in serial_dashboard.allowed_rollover:
            click.echo(f"    {ro}", err=True)

        click.echo("")

        return False
    else:
        return True


def _check_inputtype_cli(inputtype):
    if inputtype not in ["ascii", "bytes"]:
        click.echo("  ERROR", err=True)
        click.echo(
            f'  Inputted input type "{inputtype}" is not allowed. Must be either "ascii" or "bytes".',
            err=True,
        )

        click.echo("")

        return False
    else:
        return True


def _check_glyph_cli(glyph):
    if glyph not in serial_dashboard.allowed_glyphs:
        click.echo("  ERROR", err=True)
        click.echo(
            f'  Inputted glyph "{glyph}" is not allowed. Allowed glyph choises are: ',
            err=True,
        )

        for g in serial_dashboard.allowed_glyphs:
            click.echo(f"    {g}", err=True)

        click.echo("")

        return False
    else:
        return True


def _check_inputs_cli(
    baudrate, maxcols, delimiter, timecolumn, timeunits, rollover, glyph, inputtype,
):
    inputtype = inputtype.lower()

    results = [
        _check_baudrate_cli(baudrate),
        _check_maxcols_cli(maxcols),
        _check_delimiter_cli(delimiter),
        _check_timecolumn_cli(timecolumn, maxcols),
        _check_timeunits_cli(timeunits),
        _check_rollover_cli(rollover),
        _check_glyph_cli(glyph),
        _check_inputtype_cli(inputtype),
    ]

    for res in results:
        if not res:
            return False

    return True


@click.command()
@click.option(
    "--port",
    default=5006,
    type=int,
    help="port at localhost for serving dashboard (default 5006)",
)
@click.option(
    "--browser",
    default=None,
    help="browser to use for dashboard (defaults to OS default)",
)
@click.option(
    "--baudrate",
    default=115200,
    type=int,
    help="baud rate of serial connection (default 115200)",
)
@click.option(
    "--maxcols",
    default=10,
    type=int,
    help="maximum number of columns of data coming off of the board (default 10)",
)
@click.option(
    "--delimiter",
    default="comma",
    help="delimiter of data coming off of the board (default comma)",
)
@click.option(
    "--columnlabels",
    default="",
    help="labels for columns using delimiter specified with --delimiter flag (default is none)",
)
@click.option(
    "--timecolumn",
    default="none",
    help="column (zero-indexed) of incoming data that specifies time (default none)",
)
@click.option(
    "--timeunits", default="ms", help="units of incoming time data (default ms)"
)
@click.option(
    "--rollover",
    default=400,
    type=int,
    help="number of data points to be shown on a plot for each column (default 400)",
)
@click.option(
    "--glyph",
    default="lines",
    help="which glyphs to display in the plotter; either lines, dots, or both (default lines)",
)
@click.option(
    "--inputtype",
    default="ascii",
    help="whether input is ascii or bytes (default ascii)",
)
@click.option("--fileprefix", default="_tmp", help="prefix of output files")
@click.option(
    "--daqdelay",
    default=90,
    type=int,
    help="approximate delay in milliseconds for data acquisition from the board (default 20)",
)
@click.option(
    "--streamdelay",
    default=90,
    type=int,
    help="delay in milliseconds between updates of the plotter and monitor (default 90)",
)
@click.option(
    "--portsearchdelay",
    default=1000,
    type=int,
    help="delay in milliseconds for checks of serial devices (default 1000)",
)
def cli(
    port,
    browser,
    baudrate,
    maxcols,
    delimiter,
    columnlabels,
    timecolumn,
    timeunits,
    rollover,
    glyph,
    inputtype,
    fileprefix,
    daqdelay,
    streamdelay,
    portsearchdelay,
):
    """Launch a serial dashboard from the command line."""

    if _check_inputs_cli(
        baudrate, maxcols, delimiter, timecolumn, timeunits, rollover, glyph, inputtype,
    ):
        serial_dashboard.launch(
            port=port,
            browser=browser,
            baudrate=baudrate,
            maxcols=maxcols,
            delimiter=delimiter,
            columnlabels=columnlabels,
            timecolumn=timecolumn,
            timeunits=timeunits,
            rollover=rollover,
            glyph=glyph,
            inputtype=inputtype,
            fileprefix=fileprefix,
            daqdelay=daqdelay,
            streamdelay=streamdelay,
            portsearchdelay=portsearchdelay,
        )
