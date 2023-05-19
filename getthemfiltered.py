"""
/***************************************************************************
 Get them filtered
 A QGIS plugin by Pedro Camargo

        First developed     2019/09/02
        copyright           Pedro Camargo
        contact             c@margo.co
        contributors        Pedro Camargo
 ***************************************************************************/
"""

from __future__ import absolute_import
import os.path
from qgis.PyQt.QtCore import Qt, QSettings, QTranslator, qVersion, QCoreApplication
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from .get_them_filtered_dialog import GetThemFilteredDialog


class getThemFiltered:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.icon_path = os.path.join(self.plugin_dir, 'icon.svg')
        self.actions = []
        self.menu = self.tr(u'&GetThemFiltered')

        self.toolbar = self.iface.addToolBar(u'GetThemFiltered')
        self.toolbar.setObjectName(u'GetThemFiltered')
        
        self.pluginIsActive = False
        self.dockwidget = None

    def tr(self, message):
        """
        Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GetThemFiltered', message)

    # noinspection PyPep8Naming
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        """Add a toolbar icon to the toolbar."""
        icon = QIcon(self.icon_path)
        self.panelAction = QAction(icon, self.tr(u'GetThemFiltered'), self.iface.mainWindow())
        self.panelAction.triggered.connect(self.run)
        self.panelAction.triggered.connect(self.openWidget)
        self.panelAction.setCheckable(True)
        self.panelAction.setEnabled(True)

        self.toolbar.addAction(self.panelAction)
        self.iface.addPluginToMenu(self.menu, self.panelAction)
        self.actions.append(self.panelAction)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&GetThemFiltered'), action)
            self.iface.removeToolBarIcon(action)

    def widgetVisibilityChanged(self, visible: bool) -> None:
        self.panelAction.setChecked(visible)

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        self.pluginIsActive = False

    def openWidget(self, show: bool) -> None:
        self.dockwidget.setVisible(show)

    def run(self):
        if not self.pluginIsActive:
            self.pluginIsActive = True
            if self.dockwidget is None:
                self.dockwidget = GetThemFilteredDialog(self.iface)
            self.dockwidget.visibilityChanged.connect(self.widgetVisibilityChanged)

            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            self.iface.addDockWidget(
                area=Qt.LeftDockWidgetArea,
                dockwidget=self.dockwidget,
            )
