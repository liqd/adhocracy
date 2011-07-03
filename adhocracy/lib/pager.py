import urllib
import math
import logging

from formencode import validators
from pylons.i18n import _
from pylons import request, tmpl_context as c

from adhocracy.lib.templating import render_def
from adhocracy.lib import sorting, tiles

log = logging.getLogger(__name__)

PAGE_VALIDATOR = validators.Int(min=1, not_empty=True)
SIZE_VALIDATOR = validators.Int(min=1, max=250, not_empty=True)


class NamedPager(object):
    """
    A ``NamedPager`` is a list generator for the UI. The ``name`` is required
    in order to distinguish multiple pagers working on the same page.
    """

    def __init__(self, name, items, itemfunc, initial_size=10,
                 size=None, sorts={}, default_sort=None, enable_sorts=True,
                 enable_pages=True, **kwargs):
        self.name = name
        self._items = items
        self.itemfunc = itemfunc
        self.initial_size = initial_size
        if size is not None:
            self.size = size
        elif c.user and c.user.page_size:
            self.size = c.user.page_size
        else:
            self.size = initial_size
        self.sorts = sorts
        if len(sorts.values()):
            self.selected_sort = sorts.values().index(default_sort) + 1
        else:
            self.selected_sort = 0
        self.sorted = False
        self.enable_sorts = enable_sorts
        self.enable_pages = enable_pages
        self.kwargs = kwargs
        self._parse_request()

    def _parse_request(self):
        try:
            page_value = request.params.get("%s_page" % self.name)
            self.page = PAGE_VALIDATOR.to_python(page_value)
        except:
            self.page = 1

        try:
            size_value = request.params.get("%s_size" % self.name)
            self.size = SIZE_VALIDATOR.to_python(size_value)
        except:
            pass

        try:
            sort_validator = validators.Int(min=1, max=len(self.sorts.keys()),
                                            not_empty=True)
            sort_value = request.params.get("%s_sort" % self.name)
            self.selected_sort = sort_validator.to_python(sort_value)
        except:
            pass

    @property
    def items(self):
        if not self.sorted and len(self.sorts.values()):
            sorter = self.sorts.values()[self.selected_sort - 1]
            self._items = sorter(self._items)
            self.sorted = True
        return self._items[self.offset:self.offset + self.size]

    @property
    def offset(self):
        return (self.page - 1) * self.size

    @property
    def pages(self):
        return int(math.ceil(len(self._items) / float(self.size)))

    def serialize(self, page=None, size=None, sort=None, **kwargs):
        query = dict(request.params.items())
        query.update(self.kwargs)
        query.update(kwargs)
        query["%s_page" % self.name] = page if page else 1
        query["%s_size" % self.name] = size if size else self.size
        query["%s_sort" % self.name] = sort if sort else self.selected_sort

        query = dict([(str(k), unicode(v).encode('utf-8')) \
                      for k, v in query.items()])
        return "?" + urllib.urlencode(query.items())

    def here(self):
        return render_def('/pager.html', 'namedpager', pager=self)

    def to_dict(self):
        return self.items

    def __len__(self):
        return len(self.items)


def instances(instances):
    return NamedPager('instances', instances, tiles.instance.row,
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest,
                             _("activity"): sorting.instance_activity,
                             _("alphabetically"): sorting.delegateable_label},
                      default_sort=sorting.instance_activity)


def proposals(proposals, default_sort=None, **kwargs):
    if default_sort is None:
        default_sort = sorting.proposal_mixed
    sorts = {  # _("oldest"): sorting.entity_oldest,
             _("newest"): sorting.entity_newest,
             _("newest comment"): sorting.delegateable_latest_comment,
             _("support"): sorting.proposal_support,
             _("mixed"): sorting.proposal_mixed,
              _("alphabetically"): sorting.delegateable_label}
    return NamedPager('proposals', proposals, tiles.proposal.row, sorts=sorts,
                      default_sort=default_sort, **kwargs)


def milestones(milestones, default_sort=None, **kwargs):
    if default_sort is None:
        default_sort = sorting.milestone_time
    sorts = {  # _("oldest"): sorting.entity_oldest,
             _("by date"): sorting.milestone_time,
             _("newest"): sorting.entity_newest,
             _("oldest"): sorting.entity_oldest,
             _("alphabetically"): sorting.delegateable_title}
    return NamedPager('milestones', milestones, tiles.milestone.row,
                      sorts=sorts, default_sort=default_sort, **kwargs)


def pages(pages, detail=True, default_sort=None, **kwargs):
    if default_sort is None:
        default_sort = sorting.delegateable_title
    sorts = {_("oldest"): sorting.entity_oldest,
             _("newest comment"): sorting.delegateable_latest_comment,
             _("newest"): sorting.entity_newest,
             _("proposals"): sorting.norm_selections,
             _("alphabetically"): sorting.delegateable_title}
    return NamedPager('pages', pages, tiles.page.row, sorts=sorts,
                    default_sort=default_sort, **kwargs)


def users(users):
    sorts = {_("oldest"): sorting.entity_oldest,
             _("newest"): sorting.entity_newest,
             _("activity"): sorting.user_activity,
             _("alphabetically"): sorting.user_name}

    return NamedPager('users', users, tiles.user.row, sorts=sorts,
                      initial_size=15, default_sort=sorting.user_name)


def user_decisions(decisions):
    return NamedPager('decisions', decisions, tiles.decision.user_row,
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest},
                      default_sort=sorting.entity_newest)


def scope_decisions(decisions):
    return NamedPager('decisions', decisions, tiles.decision.scope_row,
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest},
                      default_sort=sorting.entity_newest)


def comments(comments):
    return NamedPager('comments', comments, tiles.comment.row,
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest},
                      default_sort=sorting.entity_newest)


def delegations(delegations):
    return NamedPager('delegations', delegations, tiles.delegation.row,
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest},
                      default_sort=sorting.entity_newest)


def events(events):
    return NamedPager('events', events, tiles.event.row)
