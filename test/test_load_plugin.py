from qgis.core import QgsProject

from getthemfiltered import classFactory
from getthemfiltered.getthemfiltered import getThemFiltered


def test_class_factory(qgis_iface):
    plugin = classFactory(qgis_iface)
    assert isinstance(plugin, getThemFiltered)
    assert plugin.iface is qgis_iface


def test_init_gui_and_unload(qgis_iface):
    plugin = getThemFiltered(qgis_iface)
    plugin.initGui()
    assert plugin.panelAction is not None
    assert plugin.toolbar is not None
    assert plugin.panelAction in plugin.actions

    plugin.unload()


def test_run_plugin(qgis_iface):
    plugin = getThemFiltered(qgis_iface)
    plugin.initGui()

    plugin.run(True)
    assert plugin.pluginIsActive
    assert plugin.dockwidget is not None
    assert plugin.dockwidget.isVisible()

    plugin.run(False)
    assert not plugin.dockwidget.isVisible()

    plugin.unload()


def test_unload_removes_dock_and_disconnects_project(qgis_iface, mocker):
    project = QgsProject.instance()
    signals = [project.aboutToBeCleared, project.cleared, project.loadingLayer, project.readProject]
    before = [project.receivers(signal) for signal in signals]

    plugin = getThemFiltered(qgis_iface)
    plugin.initGui()
    plugin.run(True)
    dock = plugin.dockwidget
    assert [project.receivers(signal) for signal in signals] != before

    remove_dock = mocker.spy(qgis_iface, "removeDockWidget")
    plugin.unload()
    remove_dock.assert_called_once_with(dock)
    assert plugin.dockwidget is None
    assert [project.receivers(signal) for signal in signals] == before
