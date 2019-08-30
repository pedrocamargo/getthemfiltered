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


# noinspection PyDocstring,PyPep8Naming
def classFactory(iface):
    from .getthemfiltered import getThemFiltered
    return getThemFiltered(iface)
