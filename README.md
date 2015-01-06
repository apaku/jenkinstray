Summary:
--------

jenkinstray is a simple system tray application to monitor jobs in one or more
jenkins instances.

Features:
---------

* Multiple servers can be monitored
* Jobs to watch can be configured for each server
* Combined job state shown through the icon with colors similar to standard
  jenkins installation
* indicates number of failed and unstable jobs in the systray icon
* configurable interval for polling
* job state changes are reported via balloon tip
* configurable timeout for hiding of the balloon tip
* access job pages easily from the context menu

Requirements:
-------------

* PyQt4 (for the System Tray integration/UI)
* enum34 (for the state information mapping from jenkins)
* appdirs (for determining the directory to store configuration)

How to build/run/use:
-----------------

* pyrcc4 -o jenkinstray/rcc_jenkinstray.py jenkinstray/jenkinstray.qrc
* python main.py
* right-click the system-tray icon to open the settings and configure servers to monitor
