import click

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler

import serial_dashboard


def _check_baudrate(baudrate):
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


def _check_maxcols(maxcols):
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


def _check_delimiter(delimiter):
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


def _check_timecolumn(timecolumn, maxcols):
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


def _check_timeunits(timeunits):
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


def _check_rollover(rollover):
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


def _check_inputtype(inputtype):
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


def _check_glyph(glyph):
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


def _check_inputs(
    baudrate, maxcols, delimiter, timecolumn, timeunits, rollover, glyph, inputtype,
):
    inputtype = inputtype.lower()

    results = [
        _check_baudrate(baudrate),
        _check_maxcols(maxcols),
        _check_delimiter(delimiter),
        _check_timecolumn(timecolumn, maxcols),
        _check_timeunits(timeunits),
        _check_rollover(rollover),
        _check_glyph(glyph),
        _check_inputtype(inputtype),
    ]

    for res in results:
        if not res:
            return False

    return True


@click.command()
@click.option("--port", default=5006, type=int)
@click.option("--browser", default=None)
@click.option("--baudrate", default=115200, type=int)
@click.option("--maxcols", default=10, type=int)
@click.option("--delimiter", default="comma")
@click.option("--columnlabels", default="")
@click.option("--timecolumn", default="none")
@click.option("--timeunits", default="ms")
@click.option("--rollover", default=400, type=int)
@click.option("--glyph", default="lines")
@click.option("--inputtype", default="ascii")
@click.option("--fileprefix", default="_tmp")
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
):
    """Launch dashboard from command line"""

    if _check_inputs(
        baudrate, maxcols, delimiter, timecolumn, timeunits, rollover, glyph, inputtype,
    ):
        # Build app
        app = serial_dashboard.app(
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
        )

        app_dict = {"/serial-dashboard": Application(FunctionHandler(app))}
        server = Server(app_dict, port=port)
        server.show("/serial-dashboard", browser=browser)
        server.run_until_shutdown()
