#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create instances from selected regions. Currently hardcoded for
offenekommune.de purposes.

Run this script after creating the region hierarchy.

call it with:
LD_LIBRARY_PATH=parts/geos/lib bin/adhocpy src/adhocracy/scripts/create-regional-instances.py etc/adhocracy.ini
"""

# boilerplate code. copy that
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'src/adhoracy'))
from common import create_parser, load_from_args
# /end boilerplate code

from sqlalchemy import not_

from adhocracy.lib.geo import normalize_region_name
from adhocracy.model import meta
from adhocracy.model import Instance
from adhocracy.model import Region
from adhocracy.model import User
from adhocracy.model.instance import instance_table


MAX_KEY_LENGTH = instance_table.columns.key.type.length


def removePrefix(str, prefix):
    return str[len(prefix):] if str.startswith(prefix) else str


def normalize_label(s):

    # s = removePrefix(s, 'Landkreis ')

    # impossible because of duplicate regions Leizpig, München, Rosenheim,
    # Heilbronn, Augsburg, Rostock, Passau, Regensburg, Fürth, Hof,
    # Bayreuth, Kaiserslautern, Aschaffenburg, Bamberg, Coburg, Würzburg,
    # Ansbach, Schweinfurt, Osnabrück, Kassel, Karlsruhe

    s = removePrefix(s, 'Kreis ')

    return s


def normalize_key(s):
    """ normalize_key creates a sensitive and nice subdomain url """
    key = normalize_region_name(s)

    if len(key) > MAX_KEY_LENGTH:
        print("stripping key %s with %d characters" % (key, len(key)))
        key = key[:MAX_KEY_LENGTH]
        key.rstrip(u'-')

    return key


def create_municipality(region):

    label = region.name

    # special cases ....
    if label == u'Landshut' and region.id == 62657:
        label = u'Stadt Landshut'

    if label == u'Oldenburg' and region.id == 62409:
        label = u'Stadt Oldenburg'

    if label == u'Freie Hansestadt Bremen':
        label = u'Bremen'

    label = normalize_label(label)

    key = normalize_key(label)

    if meta.Session.query(Instance).filter(Instance.key == key).count() > 0:
        print("there is already an instance with key %s" % key)
        return

    description = "Willkommen bei Kommune %s" % label

    user = meta.Session.query(User).filter(User.user_name == u'admin').one()

    locale = 'de_DE'

    instance = Instance.create(key, label, user, description, locale)

    instance.region = region

    """
     * Aktivierte Funktionen / Konfigurationen
       - Norms?
       - Milestones?
       - Final adoption voting? (Settings?)
       - Delegation
     * Vorangelegte Badges bzw. Kategorien?
    """

    instance.use_norms = False
    instance.milestones = False
    instance.allow_adopt = False

    print("instance %s created" % key)


def main():
    parser = create_parser(description=__doc__)
    args = parser.parse_args()
    load_from_args(args)

    stadtstaaten = (u'Berlin', u'Freie Hansestadt Bremen', u'Hamburg')

    stadtstaaten_q = meta.Session.query(Region).filter(Region.admin_level == 4)\
        .filter(Region.name.in_(stadtstaaten))

    a6_query = meta.Session.query(Region).filter(Region.admin_level == 6)\
        .join(Region.outer_regions, aliased=True)\
        .filter(Region.admin_level == 4)\
        .filter(not_(Region.name.in_(stadtstaaten)))

    for region in a6_query.union(stadtstaaten_q).all():

        try:
            create_municipality(region)
        except Exception, e:
            print("couldn't create instance for region %s, because of %s" %
                  (region.name, e))

    meta.Session.commit()

if __name__ == '__main__':
    sys.exit(main())
