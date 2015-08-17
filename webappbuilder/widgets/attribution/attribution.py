from webappbuilder.webbappwidget import WebAppWidget
import os
from PyQt4.QtGui import QIcon

class Attribution(WebAppWidget):

    def write(self, appdef, folder, app, progress):
        app.controls.append("new ol.control.Attribution()")
        self.addCss("attribution.css", folder, app)

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "attribution.png"))

    def description(self):
        return "Attribution"