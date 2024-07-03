.. _API:

API Reference
=============

.. currentmodule:: serial_dashboard


Dashboard builder and launcher
------------------------------
.. autosummary::
   :toctree: generated/launch
   :nosignatures:

   launch
   app


Serial communication utilities
------------------------------
.. autosummary::
   :toctree: generated/comms
   :nosignatures:

   SerialConnection
   comms.read_all
   comms.read_all_newlines
   comms.device_name
   comms.handshake_board
   comms.daq_stream
   comms.port_search


Parsers
------------------------------
.. autosummary::
   :toctree: generated/parsers
   :nosignatures:

   parsers.parse_read
   parsers.data_to_dicts
   parsers.fill_nans
   parsers.backfill_nans

