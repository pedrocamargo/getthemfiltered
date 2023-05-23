"""
---------------------------------------------------------------------------
 Get them filtered
                              -------------------
        begin                : 2019-09-01
        copyright            : Pedro Camargo
        email                : c@margo.co

"""

import contextlib
import os
import sys
from typing import Iterable, Literal, Optional, Union

import qgis
from qgis.core import QgsMapLayer, QgsProject
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import Qt, pyqtSignal

sys.modules["qgsfieldcombobox"] = qgis.gui
sys.modules["qgsmaplayercombobox"] = qgis.gui

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "forms/ui_filter.ui")
)


class GetThemFilteredDialog(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()
    plugin_id = "get_em_filtered"

    def __init__(self, iface, parent=None):
        QtWidgets.QDockWidget.__init__(self, None, Qt.WindowStaysOnTopHint)

        self.setupUi(self)
        self.iface = iface

        self.iface.projectRead.connect(self.load_saved_filter)

        self.rdo_single.toggled.connect(self.single_or_multi)
        # self.rdo_multi.toggled.connect(self.single_or_multi)

        self.cob_layer.layerChanged.connect(self.add_fields_to_cboxes)

        self.cob_field.fieldChanged.connect(self.populate_values_list)

        self.list_values.itemSelectionChanged.connect(self.value_selected)
        self.chb_zoom.toggled.connect(self.do_zooming)

        self.but_deselect_all.clicked.connect(self.deselect_all)
        self.but_select_all.clicked.connect(self.select_all)

        # Extra attributes
        self.values_loaded = False
        self.add_fields_to_cboxes()
        self.load_saved_filter()

    @property
    def layer(self) -> QgsMapLayer:
        return self.cob_layer.currentLayer()

    @layer.setter
    def layer(self, layer: QgsMapLayer) -> None:
        self.cob_layer.setLayer(layer)
        self.cob_field.setLayer(layer)

    @property
    def field(self) -> str:
        return self.cob_field.currentField()

    @field.setter
    def field(self, fieldname: Optional[str]) -> None:
        self.cob_field.setField(fieldname)
        if not fieldname:
            self.list_values.clear()

    def load_saved_filter(self) -> None:
        """
        Loads any saved filters from the project file
        """
        if self.filtering_saved:
            self.chb_go.setChecked(True)
        if self.zoom_saved:
            self.chb_zoom.setChecked(True)
        if self.single_or_multi_saved:
            self.rdo_single.setChecked(True)
        if self.layer_saved:
            self.layer = self.layer_saved
            if loaded_field := self.field_saved:
                self.field = loaded_field
                self.changed_field()
                self.populate_values_list()
                self.selected_values = self.values_saved

    @property
    def layer_saved(self) -> Optional[QgsMapLayer]:
        proj = QgsProject.instance()
        layer_id, type_conversion_ok = proj.readEntry(
            self.plugin_id,
            "layer",
        )
        return proj.mapLayer(layer_id)

    @layer_saved.setter
    def layer_saved(self, layer: QgsMapLayer) -> None:
        QgsProject.instance().writeEntry(
            self.plugin_id,
            "layer",
            layer.id(),
        )

    @property
    def field_saved(self) -> str:
        loaded_field, type_conversion_ok = QgsProject.instance().readEntry(
            self.plugin_id,
            "field",
            "",
        )
        return loaded_field

    @field_saved.setter
    def field_saved(self, field: str) -> None:
        QgsProject.instance().writeEntry(
            self.plugin_id,
            "field",
            field,
        )

    @property
    def values_saved(self) -> set[str]:
        loaded_values, type_conversion_ok = QgsProject.instance().readListEntry(
            self.plugin_id,
            "values",
        )
        return set(loaded_values)

    @values_saved.setter
    def values_saved(self, values: Iterable[str]) -> None:
        QgsProject.instance().writeEntry(self.plugin_id, "values", list(values))

    @property
    def filtering_saved(self) -> bool:
        filtering_enabled, type_conversion_ok = QgsProject.instance().readBoolEntry(
            self.plugin_id, "filtering_enabled"
        )
        return filtering_enabled

    @filtering_saved.setter
    def filtering_saved(self, value: bool) -> None:
        QgsProject.instance().writeEntryBool(
            self.plugin_id,
            "filtering_enabled",
            value,
        )

    @property
    def zoom_saved(self) -> bool:
        zoom_enabled, type_conversion_ok = QgsProject.instance().readBoolEntry(
            self.plugin_id, "zoom_to_results"
        )
        return zoom_enabled

    @zoom_saved.setter
    def zoom_saved(self, value: bool) -> None:
        QgsProject.instance().writeEntryBool(
            self.plugin_id,
            "zoom_to_results",
            value,
        )

    @property
    def single_or_multi_saved(self) -> bool:
        single_enabled, type_conversion_ok = QgsProject.instance().readBoolEntry(
            self.plugin_id, "single_select"
        )
        return single_enabled

    @single_or_multi_saved.setter
    def single_or_multi_saved(self, value: bool) -> None:
        QgsProject.instance().writeEntryBool(
            self.plugin_id,
            "single_select",
            value,
        )

    def save_filter(self) -> None:
        """
        Saves the current filter settings to the project file
        """
        self.layer_saved = self.layer
        self.field_saved = self.field
        self.values_saved = self.selected_values
        self.filtering_saved = self.chb_go.isChecked()
        self.zoom_saved = self.chb_zoom.isChecked()
        self.single_or_multi_saved = self.rdo_single.isChecked()

    def validate_layer(self) -> bool:
        if self.layer is None:
            self.list_values.clear()
            return False
        if self.layer not in QgsProject.instance().mapLayers().values():
            self.list_values.clear()
            return False
        return isinstance(self.layer, qgis.core.QgsVectorLayer)

    def single_or_multi(self) -> None:
        if self.rdo_single.isChecked():
            self.deselect_all()
            self.list_values.setSelectionMode(
                QtWidgets.QAbstractItemView.SingleSelection
            )
        else:
            self.list_values.setSelectionMode(
                QtWidgets.QAbstractItemView.MultiSelection
            )

    def add_fields_to_cboxes(self) -> None:
        self.reset_filter()
        if self.validate_layer():
            self.cob_field.setLayer(self.layer)
            self.field = None
            self.changed_field()
        elif not isinstance(self.layer, qgis.core.QgsVectorLayer):
            self.layer = None

    def changed_field(self) -> None:
        self.reset_filter()

    def reset_filter(self) -> None:
        if self.validate_layer():
            self.layer.setSubsetString("")

    def populate_values_list(self) -> None:
        self.list_values.clear()

        idx = self.layer.dataProvider().fieldNameIndex(self.field)
        values = sorted(str(value) for value in self.layer.uniqueValues(idx))
        table.addItems(values)
        if self.values_loaded:
            self.select_all()
        self.values_loaded = True

    def do_zooming(self) -> None:
        if self.chb_zoom.isChecked():
            self.iface.setActiveLayer(self.layer)
            self.iface.zoomToActiveLayer()

    def value_selected(self) -> None:
        if self.chb_go.isChecked():
            if l := self.selected_values:
                self.apply_filter(l)

    def apply_filter(self, list_of_values: Union[Iterable[str], Literal[True]]) -> None:
        if not self.validate_layer():
            return

        if not list_of_values:
            # Return nothing
            filter_expression = "TRUE = FALSE"
        elif list_of_values is True or self.all_selected:
            filter_expression = ''
        else:
            formatted_list_of_values = ', '.join(
                f"'{value}'" for value in list_of_values
            )
            filter_expression = f'"{self.field}" IN ({formatted_list_of_values})'
        self.layer.setSubsetString(filter_expression)

        self.do_zooming()

    def deselect_all(self) -> None:
        self.list_values.clearSelection()
        self.apply_filter([])

    def select_all(self) -> None:
        self.list_values.selectAll()
        self.apply_filter(True)

    @property
    def all_selected(self) -> bool:
        return all(
            item.isSelected()
            for item in self.list_values.findItems('*', Qt.MatchWildcard)
        )

    @property
    def selected_values(self) -> list[str]:
        return [item.text() for item in self.list_values.selectedItems()]

    @selected_values.setter
    def selected_values(self, input_values: Iterable[str]) -> None:
        self.list_values.clearSelection()
        for value in input_values:
            with contextlib.suppress(IndexError):
                self.list_values.findItems(value, Qt.MatchExactly)[0].setSelected(True)
        self.value_selected()

    def closeEvent(self, event) -> None:
        self.save_filter()
        self.closingPlugin.emit()
        event.accept()
