import click

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler

import serial_dashboard

# Build app
app = serial_dashboard.app()


@click.command()
def cli():
    """Launch dashboard from command line"""
    app_dict = {'/serial-dashboard': Application(FunctionHandler(app))}
    server = Server(app_dict, port=5006)
    server.show('/serial-dashboard')
    server.run_until_shutdown()


