from PySide.QtCore import *
from PySide.QtGui import *

import mbotenv

__all__ = [
    'loggingTreeItem'
]

LOG = mbotenv.get_logger(__name__)

class loggingTreeItem(QObject):
    def __init__(self, logger, parent=None, children=None):
        self.parent = parent
        self.logger = logger
        self.children = []
        if children != None:
            self.addChildren(children)
 
    def addChildren(self, children):
        children = asList(children)
        self.children.extend(children)