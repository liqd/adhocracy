OpenLayers in Adhocracy
=======================

OpenLayers is currently distributed along with Adhocracy, as this allows for
deployements of custom builds with limited scope and size.

It can then be deployed as a fanstatic resource, allowing for efficient
caching.

The creation of this fanstatic resource could be done in `adhocracy.buildout`,
but isn't, as compilation of the minified version is done with the `closure
compiler`, which uses Java. Therefore this is done manually as described below
and needs to be repeated when upgrading OpenLayers.


How to build OpenLayers fanstatic resource
------------------------------------------

Download and extract OpenLayers::

    wget http://openlayers.org/download/OpenLayers-2.12.tar.gz
    tar xf OpenLayers-2.12.tar.gz
    cd OpenLayers-2.12


Download closure compiler and put stuff into place (as described in
`build/README.txt`)::

    wget http://closure-compiler.googlecode.com/files/compiler-latest.zip
    unzip compiler-latest.zip compiler.jar
    mv compiler.jar tools/closure-compiler.jar
    rm compiler-latest.zip


Put the Adhocracy OpenLayers config into place. This defines which OpenLayers
modules are to be included in the build::

    # FIXME: Check final location of the config file
    cp .../openlayers-adhocracy.cfg build
    cd build


Build::

    python build.py -c closure openlayers-adhocracy openlayers.min.js
    python build.py -c done openlayers-adhocracy openlayers.js


Manipulate Openlayers theme path, because `_getScriptLocation` doesn't work
when OpenLayers is loaded asynchroneously, see `OpenLayers Issue 2470`_::

    sed -i openlayers.min.js openlayers.js -e "s|OpenLayers._getScriptLocation()|\"/fanstatic/openlayers/:version:2.12.0/\"|g"


Create static directory with files to be served::

    cd ..
    mkdir openlayers
    mv build/openlayers.min.js build/openlayers.js openlayers
    cp -a img theme openlayers
    

You can now replace the `openlayers` directory in the Adhocracy `static`
directory with the newly created `openlayers` directory and update the
fanstatic resource in `adhocracy/static/__init__.py` if needed.


.. _OpenLayers Issue 564: https://github.com/openlayers/openlayers/issues/564
.. _OpenLayers Issue 2470: http://trac.osgeo.org/openlayers/ticket/2470
