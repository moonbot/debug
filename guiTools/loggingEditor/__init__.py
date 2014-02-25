#!/usr/bin/env mayapy
# encoding: utf-8

__version__ = '0.1.0'

import core
import gui

def reloadAll():
    import gui
    reload(gui)
    import core
    reload(core)

def window():
	gui.app()
