import binascii
import typing

import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from lxml import etree
import regipy
from datetime import datetime, timedelta

class RegistryModel(QAbstractItemModel):

    class TreeItem:
        def __init__(self, key: regipy.registry.NKRecord, row: int, parent=None):
            self.__key = key
            self.__row = row
            self.__parent = parent
            self.__subkeys_names = list()
            self.__raw_subkeys = dict()
            self.__subkeys = dict()
            lm = datetime(1601, 1, 1) + timedelta(microseconds=key.header['last_modified']/10)
            self.__last_modified = lm.isoformat()
            for i in key.iter_subkeys():
                self.__subkeys_names.append(i.name)
                self.__raw_subkeys[i.name] = i
            self.__subkeys_names.sort()

        def key(self) -> regipy.registry.NKRecord:
            return self.__key

        def child(self, row: int):
            name = self.__subkeys_names[row]
            if name not in self.__subkeys:
                self.__subkeys[name] = RegistryModel.TreeItem(self.__raw_subkeys[name], row, self)
            return self.__subkeys[name]

        def child_count(self):
            return self.__key.subkey_count

        def row(self):
            return self.__row if self.__parent else 0

        def columnCount(self):
            return 2

        def data(self, column: int):
            if column == 0:
                return self.__key.name
            elif column == 1:
                return self.__last_modified
            else:
                return QVariant()

        def parent(self):
            return self.__parent

    def __init__(self, filename: Path):
        super(RegistryModel, self).__init__()
        self.__filename = filename
        self.__hive = regipy.registry.RegistryHive(filename)
        self.__root = RegistryModel.TreeItem(self.__hive.root, 0, None)
        self.__items = dict()

    def headerData(self, section: int, orientation, role=None):
        data = [
            "Name", "Last modified"
        ]
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return data[section]
        return QVariant()

    def itemData(self, index: QModelIndex):
        return self.__root

    def tree_item_at(self, index: QModelIndex):
        if index and index.isValid():
            return self.__items.get(index.internalId())
        else:
            return self.__root

    def data(self, index: QModelIndex, role=None):
        if not index or not index.isValid():
            return QVariant()

        if role != Qt.DisplayRole:
            return QVariant()

        item = self.__items.get(index.internalId())
        return item.data(index.column())

    def columnCount(self, parent:QModelIndex=None, *args, **kwargs):
        if parent and parent.isValid():
            _id = parent.internalId()
            parent_item = self.__items[_id]
            return parent_item.columnCount()
        else:
            return self.__root.columnCount()

    def rowCount(self, parent: QModelIndex=None, *args, **kwargs):
        if parent and parent.column() > 0:
            return 0

        if parent and parent.isValid():
            _id = parent.internalId()
            item = self.__items[_id]
            return item.child_count()
        else:
            return self.__root.child_count()

    def index(self, row: int, column: int, parent: QModelIndex=None, *args, **kwargs) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if parent and parent.isValid():
            _id = parent.internalId()
            parent_item = self.__items[_id]
        else:
            parent_item = self.__root

        child_item = parent_item.child(row)
        if id(child_item) not in self.__items:
            self.__items[id(child_item)] = child_item

        if child_item:
            return self.createIndex(row, column, id(child_item))

    def parent(self, index: QModelIndex=None) -> QModelIndex:
        if index is None:
            return QModelIndex()

        child_item = self.__items.get(index.internalId())
        parent_item = child_item.parent()

        if parent_item and parent_item != self.__root:
            return self.createIndex(child_item.row(), 0, parent_item)
        else:
            return QModelIndex()

    def hasChildren(self, parent=None, *args, **kwargs):
         return True

    def flags(self, index: QModelIndex):
        if index and index.isValid():
            return super(RegistryModel, self).flags(index)
        else:
            return Qt.NoItemFlags

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("layout.ui", self)

        action = self.findChild(QAction, "actionExit")
        action.triggered.connect(self.action_exit)

        action = self.findChild(QAction, "actionOpen")
        action.triggered.connect(self.action_open)

        self.__tab_widget = self.findChild(QTabWidget, "tabWidget")
        self.__tab_widget.removeTab(0)
        self.__tab_widget.removeTab(0)
        self.__tab_widget.tabCloseRequested.connect(lambda idx: self.close_tab(idx))

        self.__details = self.findChild(QTreeWidget, "detailsView")

        splitter = self.findChild(QSplitter, "splitter")
        splitter.setStretchFactor(0, 3)

        self.__files = dict()

    def open_file(self, filename: str):
        index = -1
        if filename in self.__files.keys():
            index = self.__files[filename]
        else:
            new_tab = QWidget()
            index = self.__tab_widget.addTab(new_tab, Path(filename).name)
            layout = QVBoxLayout()
            new_tab.setLayout(layout)

            splitter = QSplitter()
            treeview = QTreeView()
            treeview.setObjectName("treeview")
            treeview.setModel(RegistryModel(Path(filename)))

            dataview = QTableWidget()
            dataview.setObjectName("dataview")
            dataview.insertColumn(0)
            dataview.insertColumn(1)
            dataview.insertColumn(2)

            dataview.setContextMenuPolicy(Qt.CustomContextMenu)
            dataview.customContextMenuRequested.connect(lambda pos: self.customContextMenuRequested(dataview, pos))

            splitter.addWidget(treeview)
            splitter.addWidget(dataview)
            layout.addWidget(splitter)

            treeview.activated.connect(lambda index: self.item_selected(treeview.model().tree_item_at(index), dataview))
            self.__files[filename] = index

        assert index != -1
        self.__tab_widget.setCurrentIndex(index)

    def customContextMenuRequested(self, dataview: QTableWidget, pos: QPoint):
        index = dataview.indexAt(pos)
        menu = QMenu(dataview)
        copyAction = menu.addAction("Copy")
        copyAction.setShortcut("Ctrl+C")

        action = menu.exec_(dataview.mapToGlobal(pos))
        if action == copyAction:
            clipboard = QApplication.clipboard()
            clipboard.setText(dataview.itemAt(pos).text())

    def item_selected(self, item: RegistryModel.TreeItem, dataview: QTableWidget):
        key = item.key()
        dataview.clear()
        dataview.setHorizontalHeaderItem(0, QTableWidgetItem("Name"))
        dataview.setHorizontalHeaderItem(1, QTableWidgetItem("Value"))
        dataview.setHorizontalHeaderItem(2, QTableWidgetItem("Value type"))
        row = 0
        for v in key.iter_values():
            dataview.insertRow(row)
            name = QTableWidgetItem(v.name)
            value_type = QTableWidgetItem(v.value_type)
            if isinstance(v.value, str):
                value = QTableWidgetItem(v.value)
            elif isinstance(v.value, int):
                value = QTableWidgetItem(str(v.value))
            elif isinstance(v.value, bytes):
                _value = v.value
                try:
                    value = QTableWidgetItem(bytes.decode(_value, "ASCII"))
                except UnicodeError:
                    value = QTableWidgetItem(bytes.hex(_value))

            dataview.setItem(row, 0, name)
            dataview.setItem(row, 1, value)
            dataview.setItem(row, 2, value_type)

            row += 1
        while row < dataview.rowCount():
            dataview.removeRow(row)
        dataview.resizeColumnsToContents()
        dataview.resizeRowsToContents()
        dataview.show()

    def close_tab(self, index):
        self.__tab_widget.removeTab(index)
        tmp = dict()
        for filename, idx in self.__files.items():
            if idx != index:
                tmp[filename] = self.__files[filename]
        self.__files = tmp

    def action_exit(self):
        self.close()

    def action_open(self):
        dlg = QFileDialog()
        dlg.setAcceptMode(QFileDialog.AcceptOpen)
        dlg.setFileMode(QFileDialog.ExistingFile)
        #dlg.setNameFilter("Windows event log files (*)")
        filenames = list()
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            assert len(filenames) == 1
            self.open_file(filenames[0])


def run_app():
    app = QApplication([])

    wnd_main = MainWindow()
    wnd_main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run_app()
