"""DEPRECATED - safe to delete.

The simulation was split into:
    parameters.py  -> ADCSParams, default_params
    simulator.py   -> simulate, sizing_summary

This module only re-exports them for backward compatibility; nothing in the
project imports it any more.
"""
from .parameters import ADCSParams, default_params  # noqa: F401
from .simulator import simulate, sizing_summary       # noqa: F401
