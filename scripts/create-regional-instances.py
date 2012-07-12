#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create instances from selected regions. Currently hardcoded for
offenekommune.de purposes.

call it with:
LD_LIBRARY_PATH=parts/geos/lib bin/adhocpy src/adhocracy/scripts/create-regional-instances.py etc/adhocracy.ini
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
from adhocracy.model import Region
from adhocracy.model import User


replacements = {
    u'ä': u'ae',
    u'ö': u'oe',
    u'ü': u'ue',
    u'Ä': u'Ae',
    u'Ö': u'Oe',
    u'Ü': u'Ue',
    u'ß': u'ss',
    u' ': u'_',
    u'.': u'_',
    u'(': u'',
    u')': u'',
    }


# current setting in instance
MAX_KEY_LENGTH = 20


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
    """ make region names a sensitive and nice subdomain url """
    return reduce(lambda a, kv: a.replace(*kv), replacements.iteritems(),
            s.lower())

def create_municipality(region):

    print("creating %s"%region.name)

    label = region.name

    # special cases ....
    if label == u'Landshut' and region.id == 62657:
        label = u'Stadt Landshut'

    if label == u'Oldenburg' and region.id == 62409:
        label = u'Stadt Oldenburg'

    label = normalize_label(label)

    key = normalize_key(label)[:MAX_KEY_LENGTH]

    if meta.Session.query(Instance).filter(Instance.key==key).count()>0:
        print("there is already an instance with key %s"%key)
        import ipdb; ipdb.set_trace()
        return

    description = "Willkommen bei Kommune %s"%label

    user = meta.Session.query(User).filter(User.user_name==u'admin').one()

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

    print("instance %s created"%key)


def main():
    parser = create_parser(description=__doc__)
    args = parser.parse_args()
    load_from_args(args)

    for region in meta.Session.query(Region).filter(Region.admin_level==6):

        try:
            create_municipality(region)
        except Exception, e:
            print("couldn't create instance for region %s, because of %s"%(region.name,e))

    meta.Session.commit()

if __name__ == '__main__':
    sys.exit(main())
