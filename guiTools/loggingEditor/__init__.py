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

_WINDOW = None
def window(parent=None):
    """
    Start the Scene Dependencies Window
    """
    global _WINDOW
    if _WINDOW == None:
        wnd = gui.QLoggingEditor(parent=parent)
        _WINDOW = wnd
    if _WINDOW.isVisible() == False: 
        _WINDOW.show()
    else:
        _WINDOW.activateWindow()
    return _WINDOW

def app():
    app = QApplication(sys.argv)
    app.setApplicationName('Logging Editor')
    #app.setStyle(qt.QCustomStyle())
    win = window()
    win.onClose.connect(app.quit)
    win.activateWindow()
    win.raise_()
    sys.exit(app.exec_())

if __name__ == '__main__':
    app()
