from qgis.core import (
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt import QtCore, QtWidgets

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
    dialog.apply_filter(["A"])
    assert layer.subsetString() == "\"category\" = 'A'"

    # Test multi selection mode
    dialog.rdo_multi.setChecked(True)
    dialog.single_or_multi()
    assert dialog.list_values.selectionMode() == QtWidgets.QAbstractItemView.SelectionMode.MultiSelection

    # Test filtering multiple values
    dialog.apply_filter(["A", "B"])
    assert layer.subsetString() == "\"category\" = 'A' OR \"category\" = 'B'"

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
