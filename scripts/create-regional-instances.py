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

from adhocracy.model import meta
from adhocracy.model import Instance
from adhocracy.model import Region
from adhocracy.model import User
from adhocracy.model import CategoryBadge
from adhocracy.model.instance import instance_table
from adhocracy.model.region import normalize_region_name


MAX_KEY_LENGTH = instance_table.columns.key.type.length

UPDATE_INSTANCES = True

DESCRIPTION = u"""
Willkommen auf OffeneKommune %(label)s, der freien Beteiligungsplattform Ihrer Region!
 
OffeneKommune steht als neutrale Beteiligungsplattform allen Bürger/innen, gesellschaftlichen Akteuren und Gruppierungen offen und fördert so den direkten Dialog.
 
Egal, ob Sie Einzelperson oder Initiative, jung oder alt, Vertreterin eines Unternehmens oder einer Stadtverwaltung, mit oder ohne Wahlrecht sind, können Sie Ihre Anliegen über OffeneKommune voranbringen, oder Ihre Vorhaben mit Betroffenen und Interessierten diskutieren. Über die Themen entscheiden Sie als Nutzer/in - OffeneKommune bietet dafür die neutrale Infrastruktur.
 
Bürgerinitiativen, Vereine, Interessensverbände, Unternehmen, Politik und Verwaltung haben außerdem die Möglichkeit, OffeneKommune für ihre eigenen Beteiligungsprojekte und politischen Forderungen <strong><a href="https://offenekommune.de/_pages/engagieren/offiziell-nutzen/">offiziell zu nutzen</a></strong>.
 
Wichtig ist uns, dass alle Bürger/innen OffeneKommune heute und in Zukunft frei nutzen können. Daher betreiben wir das Projekt als <strong><a href="https://offenekommune.de/_pages/about/uber-offenekommune-de/">gemeinnütziger Träger</a></strong> und entwickeln die zugrundeliegende freie Software <strong><a href="https://bitbucket.org/liqd/adhocracy/">Adhocracy</a></strong> kontinuierlich nach den Bedürfnissen der Nutzer/innen weiter. Über Ihre <strong><a href="https://offenekommune.de/_pages/engagieren/mitarbeiten/">Mitarbeit</a></strong> und <strong><a href="https://offenekommune.de/_pages/engagieren/spenden/">Unterstützung</a></strong> freuen wir uns sehr!
 
Erfahren Sie mehr zur <strong><a href="https://offenekommune.de/_pages/engagieren/offiziell-nutzen/">offizellen Nutzung</a></strong>, zur <strong><a href=https://offenekommune.de/_pages/about">Idee hinter OffeneKommune</a></strong> oder treten Sie direkt mit uns in <strong><a href="https://offenekommune.de/_pages/about/kontakt/">Kontakt</a>.
 
Ihr Team vom Liquid Democracy e.V.
"""


def create_municipality(region):

    def removePrefix(str, prefix):
        return str[len(prefix):] if str.startswith(prefix) else str

    def normalize_label(label, region):

        # normalizing

        label = removePrefix(label, 'Kreis ')

        if label.startswith(u'Landkreis '):
            name = removePrefix(label, u'Landkreis ')

            # regions which exist with and without 'Landkreis' prefix
            if name not in [
                u'Ansbach', u'Aschaffenburg', u'Augsburg', u'Bamberg',
                u'Bayreuth', u'Coburg', u'Fürth', u'Heilbronn', u'Hof',
                u'Kaiserslautern', u'Karlsruhe', u'Kassel', u'Leipzig',
                u'München', u'Osnabrück', u'Passau', u'Regensburg',
                u'Rosenheim', u'Rostock', u'Schweinfurt', u'Würzburg'
            ]:
                label = name

        # renaming because it these exist twice

        if label == u'Landshut' and region.id == 62657:
            label = u'Stadt Landshut'

        if label == u'Oldenburg' and region.id == 62409:
            label = u'Stadt Oldenburg'

        # just renaming

        if label == u'Freie Hansestadt Bremen':
            label = u'Bremen'

        return label

    def normalize_key(s):
        """ normalize_key creates a sensitive and nice subdomain url """
        key = normalize_region_name(s)

        if len(key) > MAX_KEY_LENGTH:
            print("stripping key %s with %d characters" % (key, len(key)))
            key = key[:MAX_KEY_LENGTH]
            key.rstrip(u'-')

        return key


    label = normalize_label(region.name, region)
    key = normalize_key(label)



    user = meta.Session.query(User).filter(User.user_name == u'admin').one()
    locale = 'de_DE'
    description = DESCRIPTION % {'label': label}

    q = meta.Session.query(Instance).filter(Instance.region_id == region.id)

    if q.count() == 0:
        print("Creating instance %s from region %s" % (key, region.name))
        instance = Instance.create(key, label, user, description, locale)

    else:
        if UPDATE_INSTANCES:
            print("Updating instance %s / region %s" % (key, region.name))

            instance = q.one()

            for attr in ['key', 'label', 'locale', 'description']:

                new = eval(attr)
                old = getattr(instance, attr)

                if new != old:

                    if attr in ['key', 'label']:
                        print 'Updating %s from %s to %s' % (attr, old, new)

                    setattr(instance, attr, new)

        else:
            print("there is already an instance with key %s" % key)
            return

    fix_categories = {
        u'Bildung': u'Bildung, Schule, Ausbildung, Lebenslanges Lernen',
        u'Bürgerbeteiligung': u'Bürgerbeteiligung, Initiativen und Ehrenamt',
        u'Energie': u'Energie und Klimapolitik',
        u'Finanzen': u'Finanzen und Bürgerhaushalt',
        u'Gesundheit': u'Gesundheit',
        u'Jugend': u'Jugend',
        u'Kultur': u'Kunst, Kultur, interkulturelles Zusammenleben, Tradition',
        u'Politik': u'Politik, Verwaltung, Parteien und Verbände',
        u'Soziales': u'Soziales, Familie, Senioren, Inklusion, Genderpolitik',
        u'Sport': u'Sport',
        u'Stadtentwicklung': u'Stadt-, Raumplanung, Wohnungsbau, Denkmalschutz',
        u'Tourismus': u'Regionaler Tourismus und Stadtmarketing',
        u'Umwelt': u'Umwelt-, Tier- und Naturschutz',
        u'Verkehr': u'Verkehr',
        u'Wirtschaft & Arbeit': u'Wirtschaftsförderung, regionale Wertschöpfung und Standortvermarktung',
    }

    current_categories = CategoryBadge.all(instance)

    for category in current_categories:
        if category.title in fix_categories.keys():

            category.description = fix_categories[category.title]
            del fix_categories[category.title]
        else:
            meta.Session.delete(category)

    for (title, description) in fix_categories.iteritems():
        CategoryBadge.create(title, '#a4a4a4', description, instance=instance)


    instance.region = region

    instance.use_norms = False
    instance.milestones = False
    instance.allow_adopt = False
    instance.allow_delegate = False



def main():
    parser = create_parser(description=__doc__)
    args = parser.parse_args()
    load_from_args(args)

    stadtstaaten = (u'Berlin', u'Freie Hansestadt Bremen', u'Hamburg')

    stadtstaaten_q = meta.Session.query(Region)\
        .filter(Region.admin_level == 4)\
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
