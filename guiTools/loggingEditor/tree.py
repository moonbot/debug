
from PySide.QtCore import *
from PySide.QtGui import *
import logging

try:
    LOG = logging.getMbotLogger('loggingEditor')
except:
    LOG = logging.getLogger('loggingEditor')

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