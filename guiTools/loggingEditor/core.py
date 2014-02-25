from PySide.QtCore import *
from PySide.QtGui import *

import logging
import mbotenv
import envtools
from envtools import cached_property

import os
import sys

LOG = mbotenv.get_logger(__name__)

__all__ = [
    'QLoggingTreeModel',
    'QLoggingTreeItem',
    'getLoggers',
]

SCRIPT_DIR = os.path.dirname(__file__)

LEVEL_MAP = [
    (10, {
        'label': "Debug",
        'icon': '{SCRIPT_DIR}/images/debug_thumb.png',
        'colorA': (100, 200, 100),
        'colorB': (150, 200, 150),
    }),
    (20, {
        'label': "Info",
        'icon': '{SCRIPT_DIR}/images/info_thumb.png',
        'colorA': (100, 100, 250),
        'colorB': (150, 150, 250),
    }),
    (30, {
        'label': "Warning",
        'icon': '{SCRIPT_DIR}/images/warning_thumb.png',
        'colorA': (200, 200, 100),
        'colorB': (200, 200, 150),
    }),
    (40, {
        'label': "Error",
        'icon': '{SCRIPT_DIR}/images/error_thumb.png',
        'colorA': (200, 100, 100),
        'colorB': (200, 150, 150),
    }),
]

def prep_levels_icons():
    for map in LEVEL_MAP:
        code, data = map
        iconPath = data.get('icon', None)
        if iconPath:
            data['pixmap'] = QPixmap(iconPath.format(SCRIPT_DIR=SCRIPT_DIR))
    return True

LoggingLevelRole = 32
LoggingLevelDataRole = 33
LoggingTreeItemRole = 34

class QTreeModel(QAbstractItemModel):
    def reload(self):
        """
        Reload the list of dependant files
        If all reload kwargs are False, all are reloaded.
        """
        del self.loggers
        self.reset()

    def rowCount(self, index):
        if not index.isValid():
            return len(self.loggers)
        else:
            data = index.internalPointer()
            return len(data.children)

    def columnCount(self, index):
        return 1

    def index(self, row, column, index=None):
        if not self.hasIndex(row, column, index):
            return QModelIndex()

        if not index.isValid():
            # Roots
            childItem = self.loggers[row]
        else:
            # Sub-Children
            childItem = index.internalPointer().children[row]
        
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        if not childItem:
            return QModelIndex()
        
        # Get row and column for the parent
        column = 0
        if childItem.parent != None:
            # Sub-Logger
            row = childItem.parent.indexOfChild(childItem)
            return self.createIndex(row, column, childItem.parent)
        else:
            return QModelIndex()

    def flags(self, index):
        if not index.isValid():
            return
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 1:
            flags |= Qt.ItemIsEditable
        return flags

    def headerData(self, column, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            labels = ['Name', 'Level']
            return labels[column]
        return None

    def data(self, index, role=Qt.DisplayRole):
        """
        Load the data associated with the supplied index
        """
    
        if not index.isValid():
            return

        treeItem = index.internalPointer()
        if role == Qt.ItemDataRole:
            return treeItem

        if role == Qt.DisplayRole:
            return treeItem.levelName


    @cached_property(0)
    def loggers(self):
        return sorted(getLoggers(), key=lambda l: l.name)


class QLoggingTreeModel(QTreeModel):
    
    def columnCount(self, index):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        """
        Load the data associated with the supplied index
        """
    
        if not index.isValid():
            return

        treeItem = index.internalPointer()
        if role == LoggingTreeItemRole:
            return treeItem

        if role == LoggingLevelRole:
            return treeItem.logger.getEffectiveLevel()

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return treeItem.levelName

        if role == Qt.BackgroundRole:
            if index.column() == 1:

                try:
                    level = treeItem.logger.getEffectiveLevel()
                    if 0 <= level <= 10:
                        level = 10
                    if 11 <= level <= 20:
                        level = 20
                    if 21 <= level <= 30:
                        level = 30
                    if level >= 31:
                        level = 40
                    for map in LEVEL_MAP:
                        code, data = map
                        if code == level:
                            colorA = QColor(*data['colorA'])
                            colorB = QColor(*data['colorB'])
                            gradient = QLinearGradient()
                            gradient.setColorAt(0, colorA)
                            gradient.setColorAt(1, colorB)
                            return gradient 

                except Exception as e:
                    return

        if role == Qt.SizeHintRole:
            return QSize(50,20)

        if role == Qt.DecorationRole:
            if index.column() == 1:
                try:
                    level = treeItem.logger.getEffectiveLevel()
                    if 0 <= level <= 10:
                        level = 10
                    if 11 <= level <= 20:
                        level = 20
                    if 21 <= level <= 30:
                        level = 30
                    if level >= 31:
                        level = 40
                    for map in LEVEL_MAP:
                        code, data = map
                        if code == level:
                            return data['pixmap']
                except:
                    return

    def setData(self, index, level, role=Qt.DisplayRole):
        LOG.debug("Setting Index: {0} to {1}".format(index, level)) # TESTING
        if not index.isValid():
            return

        if index.column() == 1:

            treeItem = self.data(index, role=LoggingTreeItemRole)
            logger = treeItem.logger
            logger.setLevel(level)




class QLoggingTreeItem(QObject):
    def __init__(self, name, logger, parent=None, children=None):
        self.name = name
        self.parent = parent
        self.logger = logger
        self.children = []
        if children != None:
            self.addChildren(children)
 
    def __repr__(self):
        return "<QLoggingTreeItem {0}>".format(self.name)

    @property
    def levelName(self):
        return self.name.rsplit('.', 1)[-1]

    def addChildren(self, children):
        children = asList(children)
        # Validate the children
        for child in children:
            if not isinstance(child, QLoggingTreeItem):
                raise TypeError("Child must be a QLoggingTreeItem: {0}".format(child))
            # Set the parent of the child
            child.parent = self
        self.children.extend(children)
        # Sort the children
        self.children = sorted(self.children, key=lambda c: c.levelName)

    def indexOfChild(self, child):
        if child in self.children:
            return self.children.index(child)
'''
--------------------------------------------------------------------------------------------------------------------
'''
# QComboBoxDelegate
class QLoggingTreeDelegate(QAbstractItemDelegate):
    def paint(self, painter, option, index):
        icon = index.data(role=Qt.DecorationRole)
        gradient = index.data(role=Qt.BackgroundRole)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            gradient.setStart(*option.rect.topLeft().toTuple())
            gradient.setFinalStop(*option.rect.bottomLeft().toTuple())
            painter.fillRect(option.rect, gradient)
            centerX = option.rect.center().x() - icon.rect().width()/2
            centerY = option.rect.center().y() - icon.rect().height()/2
            painter.drawPixmap(QPoint(centerX, centerY), icon)
        except Exception as e:
            print e # TESTING
            pass

    def sizeHint(self, option, index):
        return index.data(role=Qt.SizeHintRole)

    def showLevelMenu(self):
        pass

    def setEditorData(self, editor, index):
        return

    def setModelData(self, editor, model, index):
        if index.column() == 1:
            if isinstance(editor, QLoggingLevelPopupView):
                level = editor.selectedLevel()
                model.setData(index, level, role=LoggingLevelRole)



    def editorEvent(self, event, model, option, index):
        result = super(QLoggingTreeDelegate, self).editorEvent(event, model, option, index)

        if event.type() == QEvent.MouseButtonRelease:            
            if index.column() == 1:
                selModel = self.parent().selectionModel()
                selIndexes = selModel.selectedIndexes()
                if not len(selIndexes):
                    return result                   

                w = QLoggingLevelPopupView(parent=self.parent(), useCheckboxes=False)

                for i in selIndexes:
                    w.levelChanged.connect(envtools.Callback(self.setModelData, w, model, i))

                w.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
                w.setAttribute(Qt.WA_DeleteOnClose)
                # Move the popup to the center of the cell
                childCoord = self.parent().mapToGlobal(option.rect.center()) 
                childCoord = QPoint(childCoord.x()-(w.width()/2), childCoord.y()+(w.arrowHeight*2))
                w.move(childCoord)

                w.show()
                w.list.setFocus()


        return result

class QLoggingLevelModel(QAbstractListModel):
    """
    Model of the available logging levels
    """
    PIXMAPS_CACHED = False
    useCheckboxes = False
    def __init__(self, useCheckboxes=False, *args, **kwargs):
        super(QLoggingLevelModel, self).__init__(*args, **kwargs)
        if not QLoggingLevelModel.PIXMAPS_CACHED:
            PIXMAPS_CACHED = prep_levels_icons()
        self.useCheckboxes = useCheckboxes

    def reload(self):
        """
        Reload the list of dependant files
        If all reload kwargs are False, all are reloaded.
        """
        del self.levels
        self.reset()

    def rowCount(self, index):
        if not index.isValid():
            return len(self.levels)
        return 0

    def columnCount(self, index):
        return 1

    def index(self, row, column, parent=None):
        if parent is None or not parent.isValid():
            return self.createIndex(row, column, -1)

    def flags(self, index):
        if not index.isValid():
            return
        return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role=Qt.DisplayRole):        
        if not index.isValid():
            return
        
        level, data = self.levels[index.row()]

        if role == LoggingLevelRole:
            return level

        if role == LoggingLevelDataRole:
            return (level, data)

        if role == Qt.DecorationRole:
            return data['pixmap']
    
        if role == Qt.DisplayRole:
            return data['label']

        if role == Qt.BackgroundRole:
            return QColor(*data['colorA'])

        if self.useCheckboxes == True:
            if role == Qt.CheckStateRole:
                LOG.debug(index.data(Qt.EditRole))
                value = Qt.Checked
                return value

    @cached_property(0)
    def levels(self):
        return sorted(LEVEL_MAP)


class listTest(QListView):
    def focusOutEvent(self, event):
        """
        Close the window when it loses focus
        """
        self.parent().close()
        return False

    def flags(self):
        return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable



class QArrowPopupListView(QDialog):
    """
    Arrow shaped dialog that contains a list view
    """
    arrowHeight = 12
    arrowWidth = 26
    margin = 2
    closeOnFocusOut = True

    def __init__(self, parent=None):
        super(QArrowPopupListView, self).__init__(parent=parent)

        # Set window style
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background:transparent;")

        self.spacer = QSpacerItem(self.arrowWidth, self.arrowHeight)
        
        # Setup the list view
        self.list = listTest(self)
        self.list.setAutoFillBackground(True)
        self.list.setStyleSheet("QListView { border-radius: 4px; background-color: rgb(50,50,50); }")
        self.list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Setup the layout
        lay = QVBoxLayout()
        lay.addSpacerItem(self.spacer)
        lay.addWidget(self.list)
        lay.setContentsMargins(8,8,8,8)
        self.setLayout(lay)

        # Setup sizing
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setMinimumSize(QSize(20, 20))
        self.setMaximumSize(QSize(100, 84))
        self.adjustSize()



    def listView(self):
        """
        List view for the dialog
        """
        return self.list

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(225,225,225));
        
        # Body Rectangle
        left_x = self.width() / 2 - self.arrowWidth/2 + self.margin
        path = QPainterPath()
        path.addRoundedRect(0+self.margin,0+self.arrowHeight+self.margin,self.width()-self.margin*2, self.height()-self.arrowHeight-self.margin*2, 8, 8)
        
        # Three points for the arrow
        a = QPointF(left_x, self.arrowHeight + self.margin)
        b = QPointF(left_x + self.arrowWidth/2, 0 + self.margin)
        c = QPointF(left_x + self.arrowWidth, self.arrowHeight + self.margin)

        # Create the polygon
        poly = QPolygonF()
        poly.append(a)
        poly.append(b)
        poly.append(c)
        poly.append(a)
        path.addPolygon(poly)

        painter.fillPath(path, painter.brush())
        super(QArrowPopupListView, self).paintEvent(event)


class QLoggingLevelPopupView(QArrowPopupListView):
    levelChanged = Signal(int)

    def __init__(self, parent=None, useCheckboxes=False):
        super(QLoggingLevelPopupView, self).__init__(parent=parent)

        # Setup the logging level model
        self.levelModel = QLoggingLevelModel(useCheckboxes=useCheckboxes)
        self.list.setModel(self.levelModel)

        self.levelSelectionModel = QItemSelectionModel(self.levelModel, self)
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.setSelectionModel(self.levelSelectionModel)

        self.levelSelectionModel.selectionChanged.connect(self._levelChanged)



        self.list.clicked.connect(self.close)

    def _levelChanged(self):

        self.levelChanged.emit(self.selectedLevel)

    def selectedLevel(self):

        selIndex = self.levelSelectionModel.currentIndex()
        level = selIndex.data(role=LoggingLevelRole)
        return level

    def setSelectedLevel(self, level):
        matchedIndexes = []
        for row in self.levelModel.rowCount(QModelIndex()):
            index = self.levelModel.createIndex(row, 0)
            _level = index.data(role=LoggingLevelRole)
            if _level == level:
                matchedIndexes.append(index)
        print "MatchedIndexes: {0}".format(matchedIndexes) # TESTING
        if len(matchedIndexes) > 1:
            LOG.error("Multiple matched model indexes for level: {0}".format(level))
            return
        elif len(matchedIndexes) == 0:
            LOG.error("No matching model indexes for level: {0}".format(level))
            return
        return matchedIndexes[0]

def getLoggers():
    roots = []

    def getParentForLogger(name):
        currDepth = 0
        result = None
        # Skip the last level name because it is the current logger
        levels = name.split('.')[:-1]
        LOG.debug("Levels for Logger {0}: {1}".format(name, levels))
        for levelName in levels:
            LOG.debug("Getting logger for level name: {0}".format(levelName))
            if currDepth == 0:
                LOG.debug("Searching Roots for Logger with levelName: {0}".format(levelName))
                for root in roots:
                    if root.name == levelName:
                        LOG.debug("Found root with levelName: {0}".format(levelName))
                        result = root
            else:
                LOG.debug("Searching children of {0} for logger with levelName: {1}".format(result, levelName))
                for child in result.children:
                    if child.levelName == levelName:
                        LOG.debug("Found child with levelName: {0}".format(levelName))
                        result = child
            currDepth += 1
        return result

    loggerPool = logging.root.manager.loggerDict.items()
    currDepth = 0
    while len(loggerPool):
        for i in range(0, len(loggerPool))[::-1]:
            name, logger = loggerPool[i]
            depth = name.count('.')
            if depth != currDepth:
                continue

            LOG.debug("Creating Tree Item for Logger: {0}".format(name))

            popResult = loggerPool.pop(i)
            treeItem = QLoggingTreeItem(name, logger)

            if depth == 0:
                LOG.debug("Logger is a root: {0}".format(name))
                roots.append(treeItem)
            else:
                # We are adding to loggers tha already
                # exist, so we'll just add to their children
                # attribute
                LOG.debug("Logger is a sub-logger: {0}".format(name))
                parent = getParentForLogger(name)
                LOG.debug("Got Parent {0} for logger {1}".format(parent, name))
                parent.addChildren(treeItem)
        currDepth += 1
    return roots

#--------------------------------------------------------------------------
#Line Edit Dialog
class QLineEditPopUpView(QDialog):
    arrowHeight = 12
    arrowWidth = 26
    margin = 2
    levelMaps = LEVEL_MAP

    def __init__(self, parent=None):
        super(QLineEditPopUpView, self).__init__(parent=parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background:transparent;")
        self.spacer = QSpacerItem(self.arrowWidth, self.arrowHeight)
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setAutoFillBackground(True)
        self.lineEdit.setStyleSheet("QLineEdit { border-radius: 4px; background-color: rgb(50,50,50); color: rgb(255, 255, 255);}")
        self.lineEdit.setMinimumSize(100,20)
        lay = QVBoxLayout()
        lay.addSpacerItem(self.spacer)
        lay.addWidget(self.lineEdit)
        lay.setContentsMargins(8,8,8,8)
        self.setLayout(lay)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setMinimumSize(QSize(100, 50))
        self.setMaximumSize(QSize(173, 136))
        self.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(225,225,225));
        left_x = self.width() / 2 - self.arrowWidth/2 + self.margin
        path = QPainterPath()
        path.addRoundedRect(0+self.margin,0+self.arrowHeight+self.margin,self.width()-self.margin*2, self.height()-self.arrowHeight-self.margin*2, 8, 8)
        poly = QPolygonF()
        a = QPointF(left_x, self.arrowHeight + self.margin)
        b = QPointF(left_x + self.arrowWidth/2, 0 + self.margin)
        c = QPointF(left_x + self.arrowWidth, self.arrowHeight + self.margin)
        poly.append(a)
        poly.append(b)
        poly.append(c)
        poly.append(a)
        path.addPolygon(poly)
        painter.fillPath(path, painter.brush())
        super(QLineEditPopUpView, self).paintEvent(event)


if __name__ == '__main__':
    import gui
    gui.app()

    # import sys
    # app = QApplication(sys.argv)
    # w = QLoggingLevelPopupView()
    # w.show()
    # app.exec_()
