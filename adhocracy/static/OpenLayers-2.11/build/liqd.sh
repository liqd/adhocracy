#/bin/bash

python build.py -c closure full OpenLayers-closure.js

echo "setting Openlayers image path and theme and save to OpenLayers-closure-img.js"
sed -e "s|OpenLayers.ImgPath=\"\"|OpenLayers.ImgPath=\"/OpenLayers-2.11/img/\"|" OpenLayers-closure.js > OpenLayers-closure-img.js.tmp
sed -e "s|theme/default|/OpenLayers-2.11/theme/default|" OpenLayers-closure-img.js.tmp > OpenLayers-closure-img.js
