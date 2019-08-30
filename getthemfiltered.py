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
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from .get_them_filtered_dialog import GetThemFilteredDialog


class getThemFiltered(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.icon_path = os.path.join(self.plugin_dir, 'icon.svg')
        self.dlg = GetThemFilteredDialog(self.iface)
        self.actions = []
        self.menu = self.tr(u'&GetThemFiltered')

        self.toolbar = self.iface.addToolBar(u'GetThemFiltered')
        self.toolbar.setObjectName(u'GetThemFiltered')

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
        action = QAction(icon, self.tr(u'GetThemFiltered'), self.iface.mainWindow())
        action.triggered.connect(self.run)
        action.setEnabled(True)

        self.toolbar.addAction(action)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&GetThemFiltered'), action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        self.dlg.show()
        self.dlg.exec_()