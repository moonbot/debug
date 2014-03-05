from PySide.QtCore import *
from PySide.QtGui import *

import os
import sys
import logging

import qt
import mbotenv
from envtools import cached_property

import core

__all__ = [
    'QLoggingEditor',
]

LOG = mbotenv.get_logger(__name__)

SCRIPT_DIR = os.path.dirname(__file__)
UI = os.path.join(SCRIPT_DIR, 'views/loggingEditor.ui')
base, form = qt.loadUiType(UI)

class QLoggingEditor(base, form):
    onClose = Signal()
    loggingTreeModelCls = core.QLoggingTreeModel

    executeDialog = None
    filtersDialog = None
    iconsPrepped = False

    def __init__(self, parent=None):
        base.__init__(self, parent)
        self.setupUi(self)

        # Prep Icons, so we only create pixmaps once
        if self.iconsPrepped == False:
            core.prep_levels_icons()
            self.iconsPrepped = True

        # Setup window
        self.setWindowTitle("Logging Editor")
        self.setWindowFlags(Qt.Dialog)

        # Setup tree and tree selection model
        self.loggingTreeModel = self.loggingTreeModelCls(self)
        self.loggingTreeSelectionModel = QItemSelectionModel(self.loggingTreeModel, self)
        # self.loggingTreeSelectionModel.selectionChanged.connefct(self.entitySelectionChanged)
        self.loggingTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        self.loggingTree.setModel(self.loggingTreeModel)
        self.loggingTree.setSelectionModel(self.loggingTreeSelectionModel)

        self.loggingTree.setColumnWidth(0, 400)
        self.loggingTree.setColumnWidth(1, 30)
        self.loggingTree.setEditTriggers(QAbstractItemView.CurrentChanged | QAbstractItemView.DoubleClicked)
        self.loggingTreeDelegate = core.QLoggingTreeDelegate(self.loggingTree)
        self.loggingTree.setItemDelegateForColumn(1,self.loggingTreeDelegate)

        # Connect buttons
        self.executeButton.clicked.connect(self.QExecuteDialog)
        self.filtersButton.clicked.connect(self.QFiltersDialog)
        self.refreshButton.clicked.connect(self.refresh)

    def executeCode(self):
        pass

    def refresh(self):
        model = self.loggingTree.model()
        model.reload()

    def closeEvent(self, event):
        self.onClose.emit()
        return super(QLoggingEditor, self).closeEvent(event)

    def QExecuteDialog(self):
        self.executeDialog = core.QLineEditPopUpView()
       
        self.executeDialog.setWindowFlags(self.executeDialog.windowFlags() | Qt.Popup)
        self.executeDialog.setAttribute(Qt.WA_DeleteOnClose)
        # Move the popup window into place
        parentSize = self.executeButton.pos()
        parentSize = self.mapToGlobal(parentSize)
        parentSizeX = parentSize.x()
        parentSizeY = parentSize.y()
        childCoord = QPoint(parentSizeX - 40, parentSizeY +20)
        self.executeDialog.move(childCoord)
        self.executeDialog.lineEdit.returnPressed.connect(self.runCode)
        self.executeDialog.show()
        
    def QFiltersDialog(self):
        if self.filtersDialog == None:
            core.useCheckboxes = True
            self.filtersDialog = core.QLoggingLevelPopupView(parent=self, useCheckboxes=True)
            self.filtersDialog.list.clicked.disconnect()
            LOG.debug( self.filtersDialog)
            self.filtersDialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            self.filtersDialog.setAttribute(Qt.WA_DeleteOnClose)
            LOG.debug(self.filtersDialog.list)
            #list = self.filtersDialog.listView()
            #list.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            parentSize = self.filtersButton.pos()
            parentSize = self.mapToGlobal(parentSize)
            parentSizeX = parentSize.x()
            parentSizeY = parentSize.y()
            childCoord = QPoint(parentSizeX - 10, parentSizeY + 20)
            self.filtersDialog.move(childCoord)
            self.filtersDialog.show()
        else:
            self.filtersDialog = None

    def runCode(self, clearTextField=True):
        code = self.executeDialog.lineEdit.text()
        if clearTextField:
            self.executeDialog.lineEdit.clear()
        LOG.debug("Running user code: {0}".format(code))
        if code:
            exec(code)
        self.refresh()
        self.executeDialog.hide()
