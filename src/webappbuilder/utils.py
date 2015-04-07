import os
import re
from PyQt4.QtCore import *
from qgis.core import *
import subprocess
import uuid

NO_POPUP = "NO_POPUP"
ALL_ATTRIBUTES = "ALL_ATTRIBUTES"

METHOD_FILE= 0
METHOD_WMS = 1
METHOD_WFS = 2
METHOD_WMS_POSTGIS = 3
METHOD_WFS_POSTGIS = 4
METHOD_DIRECT = 5

MULTIPLE_SELECTION_DISABLED = 0
MULTIPLE_SELECTION_ALT_KEY = 1
MULTIPLE_SELECTION_SHIFT_KEY = 2
MULTIPLE_SELECTION_NO_KEY = 3


TYPE_MAP = {
    QGis.WKBPoint: 'Point',
    QGis.WKBLineString: 'LineString',
    QGis.WKBPolygon: 'Polygon',
    QGis.WKBMultiPoint: 'MultiPoint',
    QGis.WKBMultiLineString: 'MultiLineString',
    QGis.WKBMultiPolygon: 'MultiPolygon',
    }

def tempFolder():
    tempDir = os.path.join(unicode(QDir.tempPath()), 'webappbuilder')
    if not QDir(tempDir).exists():
        QDir().mkpath(tempDir)
    return unicode(os.path.abspath(tempDir))

def tempFilenameInTempFolder(basename):
    path = tempFolder()
    folder = os.path.join(path, str(uuid.uuid4()).replace("-",""))
    if not QDir(folder).exists():
        QDir().mkpath(folder)
    filename =  os.path.join(folder, basename)
    return filename

def exportLayers(layers, folder, progress):
    epsg3587 = QgsCoordinateReferenceSystem("EPSG:3857")
    layersFolder = os.path.join(folder, "layers")
    QDir().mkpath(layersFolder)
    reducePrecision = re.compile(r"([0-9]+\.[0-9]{4})([0-9]+)")
    removeSpaces = lambda txt:'"'.join( it if i%2 else ''.join(it.split())
                         for i,it in enumerate(txt.split('"')))
    for i, appLayer in enumerate(layers):
        if appLayer.method == METHOD_FILE:
            layer = appLayer.layer
            if layer.type() == layer.VectorLayer:
                path = os.path.join(layersFolder, safeName(layer.name()) + ".js")
                QgsVectorFileWriter.writeAsVectorFormat(layer,  path, "utf-8", epsg3587, 'GeoJson')
                with open(path) as f:
                    lines = f.readlines()
                with open(path, "w") as f:
                    f.write("var %s = " % ("geojson_" + safeName(layer.name())))
                    for line in lines:
                        line = reducePrecision.sub(r"\1", line)
                        line = line.strip("\n\t ")
                        line = removeSpaces(line)
                        if layer.geometryType() == QGis.Point:
                            line = line.replace("MultiPoint", "Point")
                            line = line.replace("[[", "[")
                            line = line.replace("]]", "]")
                        f.write(line)
            elif layer.type() == layer.RasterLayer:
                orgFile = layer.source()
                destFile = os.path.join(layersFolder, safeName(layer.name()) + ".jpg")
                settings = QSettings()
                path = unicode(settings.value('/GdalTools/gdalPath', ''))
                envval = unicode(os.getenv('PATH'))
                if not path.lower() in envval.lower().split(os.pathsep):
                    envval += '%s%s' % (os.pathsep, path)
                    os.putenv('PATH', envval)
                print destFile
                subprocess.Popen(
                    ['gdal_translate -of JPEG -a_srs EPSG:3857 %s %s' % (orgFile, destFile)],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=False,
                    )
        progress.setProgress(int(i*100.0/len(layers)))


def safeName(name):
    #TODO: we are assuming that at least one character is valid...
    validChars = '123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
    return ''.join(c for c in name if c in validChars).lower()