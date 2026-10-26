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
