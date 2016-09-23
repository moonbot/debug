from Qt import QtCore, QtGui, QtWidgets

import mbotenv
import envtools

__all__ = [
    'loggingTreeItem'
]

LOG = mbotenv.get_logger(__name__)


class loggingTreeItem(QtCore.QObject):
    def __init__(self, logger, parent=None, children=None):
        self.parent = parent
        self.logger = logger
        self.children = []
        if children is not None:
            self.addChildren(children)

    def addChildren(self, children):
        children = envtools.asList(children)
        self.children.extend(children)
