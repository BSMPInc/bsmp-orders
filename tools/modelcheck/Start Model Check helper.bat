@echo off
rem Starts the BSMP Model Check helper in the background (no window).
rem The QC app's Model Check page talks to it; it runs the compare in the open SolidWorks.
rem Running it twice is harmless - the second copy sees the port is taken and exits.
start "" pythonw "%~dp0helper.py"
