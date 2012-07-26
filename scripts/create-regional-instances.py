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
from adhocracy.model import CategoryBadge
from adhocracy.model.instance import instance_table


MAX_KEY_LENGTH = instance_table.columns.key.type.length

UPDATE_INSTANCES = True

DESCRIPTION = """
Willkommen auf OffeneKommune, der freien Beteiligungsplattform Ihrer Region.

OffeneKommune steht als neutrale Beteiligungsplattform allen gesellschaftlichen Akteuren und Gruppierungen offen und ermöglicht so einen direkten Dialog zu kommunalen Anliegen. Die Plattform kann von allen Engagierten für eigene Beteiligungsprojekte, aber auch für Diskurse zwischen unterschiedlichen Ebenen genutzt werden.

Egal, ob Sie jung oder alt, mit oder ohne Wahlrecht, Einzelkämpfer oder Initiative, Vertreterin eines Unternehmens oder einer Stadtverwaltung sind, können Sie Ihre Anliegen über OffeneKommune voranbringen, oder Ihre Vorhaben mit Betroffenen und Interessierten diskutieren.

Bürgerinitiativen, Vereine, Unternehmen, Politik und Verwaltung haben die Möglichkeit OffeneKommune für eigene Beteiligungsprojekte offiziell zu nutzen und in die eigene Arbeit einzubinden. Erfahren Sie bei Interesse <a href="/_pages/mehr_erfahren">mehr</a> oder setzen Sie sich direkt mit uns in <a href="http://liqd.net/kontakt-2/kontakt-offenekommune/">Verbindung</a>!

OffeneKommune ist gezielt als neutrale Infrastruktur für offene Diskussionen und Beteiligungsverfahren ausgelegt. Es liegt an Ihnen, welche Inhalte auf der Plattform diskutiert werden. Seien dies Bauvorhaben, Zukunftsstrategien, Verbesserungsideen, Hinweise auf Missstände oder sonstige Diskussionen - auf OffeneKommune findet keine Moderation der Beiträge statt, bestimmen die Nutzer/innen durch ihre Beiträge und Bewertungen, was relevant ist.

Wichtig ist uns, dass alle Bürger/innen OffeneKommune heute und in Zukunft frei nutzen können. Daher betreiben wir das Projekt als gemeinnütziger [Träger] und entwickeln die zugrundeliegende freie Software <a href="https://bitbucket.org/liqd/adhocracy">Adhocracy</a> kontinuierlich nach den Bedürfnissen der Nutzer/innen weiter. Über Ihre [Mitarbeit] und [Unterstützung] freuen wir uns sehr!

Bei Fragen können Sie sich gerne an uns wenden. Viel Spaß beim Beteiligen!

Das Team vom Liquid Democracy e.V.
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
    description = DESCRIPTION

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
        u'Bildung': u'Bildung', 
        u'Bürgerbeteiligung': u'Bürgerbeteiligung', 
        u'Finanzen': u'Finanzen', 
        u'Gesundheit': u'Gesundheit',
        u'Infrastruktur': u'Infrastruktur', 
        u'Innenstadt': u'Innenstadt', 
        u'Jugend': u'Jugend', 
        u'Kultur': u'Kultur',
        u'Natur in der Stadt': u'Natur in der Stadt', 
        u'Politik': u'Politik', 
        u'Soziales': u'Soziales', 
        u'Sport': u'Sport',
        u'Tierschutz': u'Tierschutz', 
        u'Tourismus': u'Tourismus', 
        u'Umweltschutz': u'Umweltschutz', 
        u'Wirtschaft': u'Wirtschaft',
        u'Wohnungsbau': u'Wohnungsbau'
    }

    current_categories = CategoryBadge.all(instance)

    for category in current_categories:
        if category.title in fix_categories.keys():

            category.description = fix_categories[category.title]
            del fix_categories[category.title]
        else:
            category.delete()

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
