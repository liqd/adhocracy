#!/bin/bash 

echo "Installing Babel..."
wget http://unicode.org/Public/cldr/1.6.1/core.zip
cd ../adhocracy/contrib/babel/
./setup.py egg_info
./scripts/import_cldr.py ../../../unicode/
sudo easy_install ElementTree
sudo ./setup.py install
