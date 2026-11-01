import pytest
from qgis.core import (
    QgsCoordinateTransformContext,
    QgsFeature,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
)
from qgis.PyQt import sip
from qgis.PyQt.QtCore import Qt

from getthemfiltered.get_them_filtered_dialog import GetThemFilteredDialog


@pytest.fixture
def project():
    project = QgsProject.instance()
    yield project
    project.clear()


@pytest.fixture
def dialogs(qgis_iface):
    """Creates dialogs and deletes them afterwards, so they stop reacting to later tests' project changes."""
    created = []

    def make():
        dialog = GetThemFilteredDialog(qgis_iface)
        created.append(dialog)
        return dialog

    yield make
    for dialog in created:
        if not sip.isdeleted(dialog):
            sip.delete(dialog)


@pytest.fixture
def layer(project, tmp_path):
    """A GeoPackage point layer, so it survives a project reload."""
    memory_layer = QgsVectorLayer("Point?crs=EPSG:4326&field=name:string&field=count:integer", "points", "memory")
    features = []
    for name, count in [("a", 1), ("b", 2), ("b", 3), ("c", 3)]:
        feature = QgsFeature(memory_layer.fields())
        feature.setAttributes([name, count])
        features.append(feature)
    memory_layer.dataProvider().addFeatures(features)

    path = str(tmp_path / "points.gpkg")
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    error, *_ = QgsVectorFileWriter.writeAsVectorFormatV3(memory_layer, path, QgsCoordinateTransformContext(), options)
    assert error == QgsVectorFileWriter.WriterError.NoError

    layer = QgsVectorLayer(path, "points", "ogr")
    assert layer.isValid()
    project.addMapLayer(layer)
    return layer


@pytest.fixture
def configured_dialog(dialogs, layer):
    dialog = dialogs()
    dialog.cob_layer.setLayer(layer)
    dialog.cob_field.setField("name")
    dialog.rdo_multi.setChecked(True)
    dialog.chb_go.setChecked(True)
    dialog.chb_go.clicked.emit(True)  # setChecked() doesn't emit clicked, which triggers a save
    select(dialog, "a", "c")
    assert layer.featureCount() == 2
    return dialog


@pytest.fixture
def saved_project(project, configured_dialog, tmp_path):
    path = str(tmp_path / "project.qgz")
    assert project.write(path)
    return path


def select(dialog, *values):
    dialog.list_values.clearSelection()
    for value in values:
        dialog.list_values.findItems(value, Qt.MatchFlag.MatchExactly)[0].setSelected(True)


def reload(project, path):
    """Clears and re-reads the project, as QGIS does when opening a project file."""
    project.clear()
    assert project.read(path)


def assert_restored(dialog, project):
    (layer,) = project.mapLayersByName("points")
    assert dialog.cob_layer.currentLayer() == layer
    assert dialog.field == "name"
    assert sorted(dialog.selected_values) == ["a", "c"]
    assert dialog.chb_go.isChecked()
    assert dialog.rdo_multi.isChecked()
    assert layer.featureCount() == 2


def test_settings_written_to_project(project, configured_dialog):
    assert project.readEntry("getthemfiltered", "field")[0] == "name"
    assert configured_dialog.values_saved == {"a", "c"}
    assert configured_dialog.filtering_saved
    assert not configured_dialog.single_or_multi_saved


def test_load_into_open_dialog(project, configured_dialog, saved_project):
    reload(project, saved_project)
    assert_restored(configured_dialog, project)


def test_load_into_new_dialog(project, dialogs, configured_dialog, saved_project):
    sip.delete(configured_dialog)
    reload(project, saved_project)
    assert_restored(dialogs(), project)


def test_reload_does_not_overwrite_saved_settings(project, configured_dialog, saved_project):
    """Signals fired while the project is cleared and re-read must not save over the file's settings."""
    reload(project, saved_project)
    assert configured_dialog.field_saved == "name"
    assert configured_dialog.values_saved == {"a", "c"}


def test_saving_resumes_after_new_project(project, configured_dialog, layer):
    """Clearing without reading a project (File > New) must not leave saving paused."""
    source = layer.source()
    project.clear()
    new_layer = QgsVectorLayer(source, "points", "ogr")
    project.addMapLayer(new_layer)
    configured_dialog.cob_layer.setLayer(new_layer)
    configured_dialog.cob_field.setField("count")
    assert configured_dialog.field_saved == "count"
