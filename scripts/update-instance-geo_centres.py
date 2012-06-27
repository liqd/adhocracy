#!/usr/bin/env python
"""
Updates geo_centre field on all instances which have a region set, but no
geo_centre.

call it with:
LD_LIBRARY_PATH=parts/geos/lib bin/adhocpy src/adhocracy/scripts/update-instance-geo_centres.py etc/adhocracy.ini
"""

# boilerplate code. copy that
import os
import sys
sys.path.insert(0,  os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0,  '/home/nico/wiese/adhocracy.buildout/src/adhocracy')
from common import create_parser, get_instances, load_from_args
# /end boilerplate code

from adhocracy.model import meta
from adhocracy.model import Instance
from shapely import wkb
from shapely import wkt


def main():
    parser = create_parser(description=__doc__)
    args = parser.parse_args()
    load_from_args(args)

    for i in meta.Session.query(Instance).all():
        if i.region is not None and i.geo_centre is None:
            i.geo_centre=wkt.dumps(wkb.loads(str(i.region.boundary.geom_wkb)).centroid)

    meta.Session.commit()


if __name__ == '__main__':
    sys.exit(main())
