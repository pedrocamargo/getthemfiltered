"""
---------------------------------------------------------------------------
 Get them filtered
                              -------------------
        begin                : 2019-09-01
        copyright            : Pedro Camargo
        email                : c@margo.co

"""
from ast import literal_eval
import os
import sys

import qgis
from qgis.PyQt import QtWidgets, uic, QtGui, QtCore, QtWidgets
from qgis.PyQt.QtWidgets import *
from qgis.core import QgsProject
from qgis.PyQt.QtCore import pyqtSignal


sys.modules["qgsfieldcombobox"] = qgis.gui
sys.modules["qgsmaplayercombobox"] = qgis.gui

try:
    from qgis.core import QgsMapLayerRegistry
except ImportError:
    pass

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'forms/ui_filter.ui'))


class GetThemFilteredDialog(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()
    plugin_id = "get_em_filtered"

    def __init__(self, iface, parent=None):
        QtWidgets.QDockWidget.__init__(self, None, QtCore.Qt.WindowStaysOnTopHint)

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

        self.layer = None
        # Extra attributes
        self.field = None
        
        proj = QgsProject.instance()
        raw_layer_id, type_conversion_ok = proj.readEntry(
            self.plugin_id,
            "layer"
        )
        if raw_layer_id:
            # try:
            self.layer = QgsProject.instance().mapLayer(raw_layer_id)
            # except Exception:  # TODO More specific exception
            #     print("Get em filtered: saved layer not found in project")

        if self.layer:
            field, values = self.load_from_subset_string(self.layer.subsetString())
            if field and values:
                self.field = field
            else: 
                loaded_field, type_conversion_ok = proj.readEntry(
                    self.plugin_id,
                    "field"
                )
                if loaded_field:
                    self.field = loaded_field


        self.add_fields_to_cboxes()

    @staticmethod
    def load_from_subset_string(subset_string: str) -> tuple[str, list] | tuple[None, None]:
        #  "Jurisdiction" = 'Ashford' OR "Jurisdiction" = 'Ansonia'
        split_selectors = subset_string.split(" OR ")
        values = set()
        field = ''
        for count, item in enumerate(split_selectors):
            new_field, separator, value = item.partition(" = ")
            new_field = literal_eval(new_field)
            if count > 0 and new_field != field:
                # There should only be one value for field, if this plugin created the saved filter
                return None
            field = new_field
            value = literal_eval(value)
            values.append(value)
        return field, values
    
    def save_filter(self):
        proj = QgsProject.instance()
        proj.writeEntry(
            self.plugin_id,
            "layer",
            self.layer,
        )
        proj.writeEntry(
            self.plugin_id,
            "field",
            self.field,
        )

    def check_layer(self):
        if self.layer is None:
            self.list_values.clear()
            return False
        if self.layer not in QgsProject.instance().mapLayers().values():
            self.list_values.clear()
            return False
        return isinstance(self.layer, qgis.core.QgsVectorLayer)

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
        elif not isinstance(self.layer, qgis.core.QgsVectorLayer):
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
        values = sorted(str(value) for value in self.layer.uniqueValues(idx))
        table.addItems(values)
        self.select_all()

    def do_zooming(self):
        if self.chb_zoom.isChecked():
            self.iface.setActiveLayer(self.layer)
            self.iface.zoomToActiveLayer()

    def selected_value(self):
        if self.chb_go.isChecked():
            if l := [i.text() for i in self.list_values.selectedItems()]:
                self.apply_filter(l)

    def apply_filter(self, list_of_values):
        if not self.check_layer():
            return
        
        filter_expression = " OR ".join(
            f'"{self.field}" = \'{i}\'' for i in list_of_values
        )
        self.layer.setSubsetString(filter_expression)

        self.do_zooming()

    def deselect_all(self):
        self.list_values.clearSelection()

    def select_all(self):
        self.list_values.selectAll()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()