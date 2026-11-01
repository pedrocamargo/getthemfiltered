import pytest
from qgis.core import (
    QgsCoordinateTransformContext,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
)
from qgis.PyQt import QtCore, QtWidgets, sip

from getthemfiltered.get_them_filtered_dialog import GetThemFilteredDialog


def create_test_layer():
    """Create a temporary in-memory vector layer with sample data."""
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "test_layer", "memory")
    provider = layer.dataProvider()

    try:
        from qgis.PyQt.QtCore import QMetaType

        type_int = QMetaType.Type.Int
        type_str = QMetaType.Type.QString
    except (ImportError, AttributeError):
        type_int = QtCore.QVariant.Int
        type_str = QtCore.QVariant.String

    provider.addAttributes(
        [
            QgsField("id", type_int),
            QgsField("category", type_str),
        ]
    )
    layer.updateFields()

    features = []
    data = [(1, "A"), (2, "B"), (3, "A"), (4, "C"), (5, "B")]
    for fid, cat in data:
        feat = QgsFeature(layer.fields())
        feat.setAttribute("id", fid)
        feat.setAttribute("category", cat)
        feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(fid, fid)))
        features.append(feat)

    provider.addFeatures(features)
    layer.updateExtents()
    return layer


def test_filter_dialog_workflow(qgis_iface):
    """Test full filtering workflow with memory vector layer."""
    layer = create_test_layer()
    QgsProject.instance().addMapLayer(layer)

    dialog = GetThemFilteredDialog(qgis_iface)
    dialog.cob_layer.setLayer(layer)
    dialog.add_fields_to_cboxes()

    assert dialog.layer == layer
    dialog.cob_field.setField("category")
    dialog.changed_field()

    # Verify unique values collected: A, B, C
    assert dialog.list_values.count() == 3
    items = [dialog.list_values.item(i).text() for i in range(dialog.list_values.count())]
    assert items == ["A", "B", "C"]

    # Test single selection mode
    dialog.rdo_single.setChecked(True)
    dialog.single_or_multi()
    assert dialog.list_values.selectionMode() == QtWidgets.QAbstractItemView.SelectionMode.SingleSelection

    # Test filtering single value
    dialog.chb_go.setChecked(True)
    dialog.apply_filter(["A"])
    assert layer.subsetString() == "\"category\" IN ('A')"

    # Test multi selection mode
    dialog.rdo_multi.setChecked(True)
    dialog.single_or_multi()
    assert dialog.list_values.selectionMode() == QtWidgets.QAbstractItemView.SelectionMode.MultiSelection

    # Test filtering multiple values
    dialog.apply_filter(["A", "B"])
    assert layer.subsetString() == "\"category\" IN ('A', 'B')"

    # Test select all and deselect all
    dialog.select_all()
    assert len(dialog.list_values.selectedItems()) == 3

    dialog.deselect_all()
    assert len(dialog.list_values.selectedItems()) == 0

    # Test reset filter
    dialog.reset_filter()
    assert layer.subsetString() == ""

    # Clean up project
    QgsProject.instance().removeMapLayer(layer.id())


def make_filtering_dialog(qgis_iface, layer):
    # Earlier tests leave their settings in the shared project, and a new dialog loads them
    QgsProject.instance().clear()
    QgsProject.instance().addMapLayer(layer)
    dialog = GetThemFilteredDialog(qgis_iface)
    dialog.cob_layer.setLayer(layer)
    dialog.cob_field.setField("category")
    dialog.rdo_multi.setChecked(True)
    return dialog


def test_checking_do_filtering_applies_selection(qgis_iface):
    layer = create_test_layer()
    dialog = make_filtering_dialog(qgis_iface, layer)

    dialog.list_values.clearSelection()
    dialog.list_values.findItems("A", QtCore.Qt.MatchFlag.MatchExactly)[0].setSelected(True)
    assert layer.featureCount() == 5

    dialog.chb_go.click()
    assert layer.subsetString() == "\"category\" IN ('A')"
    assert layer.featureCount() == 2

    sip.delete(dialog)
    QgsProject.instance().removeMapLayer(layer.id())


def test_unchecking_do_filtering_removes_filter(qgis_iface):
    layer = create_test_layer()
    dialog = make_filtering_dialog(qgis_iface, layer)

    dialog.chb_go.click()
    dialog.list_values.clearSelection()
    dialog.list_values.findItems("A", QtCore.Qt.MatchFlag.MatchExactly)[0].setSelected(True)
    assert layer.featureCount() == 2

    dialog.chb_go.click()
    assert layer.subsetString() == ""
    assert layer.featureCount() == 5

    sip.delete(dialog)
    QgsProject.instance().removeMapLayer(layer.id())


@pytest.mark.parametrize("driver, extension", [("GeoJSON", "geojson"), ("ESRI Shapefile", "shp"), ("GPKG", "gpkg")])
def test_deselect_all_shows_nothing_in_file_layers(qgis_iface, tmp_path, driver, extension):
    """The OGR provider passes the filter to the file's SQL dialect, which may not know TRUE or FALSE."""
    path = str(tmp_path / f"test_layer.{extension}")
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = driver
    error, *_ = QgsVectorFileWriter.writeAsVectorFormatV3(
        create_test_layer(), path, QgsCoordinateTransformContext(), options
    )
    assert error == QgsVectorFileWriter.WriterError.NoError
    layer = QgsVectorLayer(path, "test_layer", "ogr")
    assert layer.isValid()
    dialog = make_filtering_dialog(qgis_iface, layer)

    dialog.chb_go.click()
    dialog.deselect_all()
    assert layer.subsetString() != ""
    assert layer.featureCount() == 0

    sip.delete(dialog)
    QgsProject.instance().removeMapLayer(layer.id())
