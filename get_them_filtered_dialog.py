"""
---------------------------------------------------------------------------
 Get them filtered
                              -------------------
        begin                : 2019-09-01
        copyright            : Pedro Camargo
        email                : c@margo.co

"""
import os
import sys

import qgis
from qgis.PyQt import QtWidgets, uic, QtGui, QtCore, QtWidgets
from qgis.PyQt.QtWidgets import *
from qgis.core import QgsProject

sys.modules["qgsfieldcombobox"] = qgis.gui
sys.modules["qgsmaplayercombobox"] = qgis.gui

try:
    from qgis.core import QgsMapLayerRegistry
except ImportError:
    pass

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'forms/ui_filter.ui'))


class GetThemFilteredDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, iface, parent=None):
        QtWidgets.QDialog.__init__(self, None, QtCore.Qt.WindowStaysOnTopHint)

        self.setupUi(self)
        self.iface = iface

        self.rdo_single.toggled.connect(self.single_or_multi)
        # self.rdo_multi.toggled.connect(self.single_or_multi)

        self.cob_layer.layerChanged.connect(self.add_fields_to_cboxes)

        self.cob_field.fieldChanged.connect(self.changed_field)

        self.list_values.itemSelectionChanged.connect(self.selected_value)
        self.chb_zoom.toggled.connect(self.do_zooming)

        self.but_deselect_all.clicked.connect(self.deselect_all)
        self.but_select_all.clicked.connect(self.select_all)

        # Extra attributes
        self.layer = None
        self.field = None

        self.add_fields_to_cboxes()

    def check_layer(self):
        if self.layer is None:
            self.list_values.clear()
            return False
        if self.layer not in QgsProject.instance().mapLayers().values():
            self.list_values.clear()
            return False
        if not isinstance(self.layer, qgis.core.QgsVectorLayer):
            return False
        return True

    def single_or_multi(self):
        if self.rdo_single.isChecked():
            self.deselect_all()
            self.list_values.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        else:
            self.list_values.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

    def add_fields_to_cboxes(self):
        self.reset_filter()
        self.layer = self.cob_layer.currentLayer()
        self.field = None
        if self.check_layer():
            self.cob_field.setLayer(self.layer)
            self.changed_field()
        else:
            if not isinstance(self.layer, qgis.core.QgsVectorLayer):
                self.layer = None

    def changed_field(self):
        self.reset_filter()
        self.field = self.cob_field.currentField()
        self.do_filtering()

    def reset_filter(self):
        if self.check_layer():
            self.layer.setSubsetString("")

    def do_filtering(self):
        if not self.check_layer():
            return
        table = self.list_values
        table.clear()

        idx = self.layer.dataProvider().fieldNameIndex(self.field)
        values = []
        for feat in self.layer.getFeatures():
            values.append(feat.attributes()[idx])
        values = sorted([str(x) for x in set(values)])
        table.addItems(values)
        self.select_all()
        # for v in set(values):
        #     it = QtWidgets.QListWidgetItem(str(v))
        #     table.addItem(it)
        #     it.setSelected(True)

    def do_zooming(self):
        if self.chb_zoom.isChecked():
            self.iface.setActiveLayer(self.layer)
            self.iface.zoomToActiveLayer()

    def selected_value(self):
        if self.chb_go.isChecked():
            l = [i.text() for i in self.list_values.selectedItems()]
            if l:
                self.apply_filter(l)

    def apply_filter(self, list_of_values):
        if not self.check_layer():
            return

        filter_expression = '"{}" = \'{}\''.format(self.field, list_of_values[0])
        if len(list_of_values) > 1:
            for i in list_of_values[1:]:
                filter_expression = filter_expression + ' OR "{}" = \'{}\''.format(self.field, i)
        self.layer.setSubsetString(filter_expression)

        self.do_zooming()

    def deselect_all(self):
        self.list_values.clearSelection()

    def select_all(self):
        self.list_values.selectAll()
