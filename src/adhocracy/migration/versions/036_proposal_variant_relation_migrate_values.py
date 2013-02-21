from datetime import datetime
from logging import getLogger
from pickle import dumps, loads
import re

from sqlalchemy import (MetaData, Column, ForeignKey, DateTime, Integer,
                        PickleType, String, Table, Unicode)

metadata = MetaData()

log = getLogger(__name__)


def are_elements_equal(x, y):
    return x == y


new_selection_table = Table(
    'selection', metadata,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime),
    Column('page_id', Integer, ForeignKey('page.id',
           name='selection_page', use_alter=True), nullable=True),
    Column('proposal_id', Integer, ForeignKey('proposal.id',
           name='selection_proposal', use_alter=True), nullable=True),
    Column('variants', PickleType(comparator=are_elements_equal),
           nullable=True)
    )


page_table = Table('page', metadata,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('function', Unicode(20))
    )


poll_table = Table('poll', metadata,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('action', Unicode(50), nullable=False),
    Column('subject', Unicode(254), nullable=False),
    Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False)
    )

category_graph = Table('category_graph', metadata,
    Column('parent_id', Integer, ForeignKey('delegateable.id')),
    Column('child_id', Integer, ForeignKey('delegateable.id'))
    )


delegateable_table = Table('delegateable', metadata,
    Column('id', Integer, primary_key=True),
    Column('label', Unicode(255), nullable=False),
    Column('type', String(50)),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow,
           onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('milestone_id', Integer, ForeignKey('milestone.id'), nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False)
    )

tally_table = Table('tally', metadata,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=False),
    Column('vote_id', Integer, ForeignKey('vote.id'), nullable=True),
    Column('num_for', Integer, nullable=True),
    Column('num_against', Integer, nullable=True),
    Column('num_abstain', Integer, nullable=True)
    )


now = datetime.utcnow()

SEL_RE = re.compile('\[@\[selection:([^\]]*)\],"([^"]*)"\]')


def get_tally_count(migrate_engine, poll_id):
    tallies = migrate_engine.execute(
        tally_table.select('poll_id = %s' % poll_id)).fetchall()
    tallies = sorted(tallies)
    last = tallies[-1]
    (_, _, _, _, num_for, num_against, _) = last
    tally_count = num_for + num_against
    return tally_count


def collect_selection_data(selections):
    to_proposal = {}
    to_variants = {}
    for (sid, create_time, delete_time, page_id, proposal_id,
         variants) in selections:
        if delete_time is not None and delete_time < now:
            pass
        to_proposal[sid] = proposal_id
        to_variants[sid] = loads(variants)
    return to_proposal, to_variants


def collect_poll_data(migrate_engine, polls, selection_to_proposal):
    proposal_ids = []
    variant_to_selection = {}
    for (poll_id, _, end_time, _, action, subject, scope_id) in polls:
        if action != u'select':
            continue
        if end_time is not None and end_time < now:
            continue
        match = SEL_RE.match(subject)
        selection_id = int(match.group(1))
        variant = match.group(2)
        if variant == u'HEAD':
            # we handle HEAD speacially. Every Proposal has access to
            # HEAD.
            continue
        var_selections = variant_to_selection.setdefault(variant, [])
        tally_count = get_tally_count(migrate_engine, poll_id)
        var_selections.append([tally_count, selection_id, poll_id])
        try:
            proposal_ids.append(selection_to_proposal[selection_id])
        except Exception, E:
            pass
    return proposal_ids, variant_to_selection


def handle_page(migrate_engine, page_id, selections_, polls):

    (selection_to_proposal,
     selections_to_variants) = collect_selection_data(selections_)

    (proposal_ids,
     variant_to_selection) = collect_poll_data(migrate_engine, polls,
                                               selection_to_proposal)

    # if we have proposals select a winning proposal and assign
    # the variant to it

    if not len(set(proposal_ids)):
        # no proposals
        return

    for variant, tally_selections in variant_to_selection.items():
        tally_selections = sorted(tally_selections)
        count, winning_selection, poll_id = tally_selections[-1]
        try:
            selections_to_variants[winning_selection].append(variant)
            migrate_engine.execute(
                new_selection_table.update().values(
                    variants=dumps(
                        selections_to_variants[winning_selection]))
                        .where(
                            new_selection_table.c.id == winning_selection))
        except KeyError, E:
            msg = (
                'KeyError: %s\n' % E +
                'There is no selection with the id %s \n' % E +
                'which should be the winner for ' +
                'page %s - variant %s' % (page_id, variant))
            log.error(msg)


def add_default_variant(migrate_engine):
    default_variants = [u'HEAD']
    default_variants_pickle = dumps(default_variants)
    migrate_engine.execute(
        new_selection_table.update().values(variants=default_variants_pickle))


def upgrade(migrate_engine):

    metadata.bind = migrate_engine
    page_table = Table('page', metadata, autoload=True)
    proposal_table = Table('proposal', metadata, autoload=True)

    add_default_variant(migrate_engine)

    pages = migrate_engine.execute(page_table.select())
    for (page_id, function) in pages:
        if function != u'norm':
            continue
        selections = migrate_engine.execute(
            new_selection_table.select('page_id = %s' % page_id)).fetchall()
        polls = migrate_engine.execute(
            poll_table.select('scope_id = %s' % page_id)).fetchall()
        handle_page(migrate_engine, page_id, selections, polls)

    return


def downgrade(migrate_engine):
    raise NotImplementedError()
