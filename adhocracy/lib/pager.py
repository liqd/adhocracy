import math
import logging
import urllib

from formencode import validators
from pylons.i18n import _
from pylons import request, tmpl_context as c, url
from pylons.controllers.util import redirect
from webob.multidict import MultiDict

from adhocracy import model
from adhocracy.lib import sorting, tiles
from adhocracy.lib.event.stats import user_activity
from adhocracy.lib.search.query import sunburnt_query, add_wildcard_query
from adhocracy.lib.templating import render_def


log = logging.getLogger(__name__)

PAGE_VALIDATOR = validators.Int(min=1, not_empty=True)
SIZE_VALIDATOR = validators.Int(min=1, max=250, not_empty=True)


def visible_pages(selected_page, pages):
    '''
    determinate which page links in a pager are visible
    and where the '...' seperators should be located.
    **Warning**: This code is 1-based!

    *selected_page*
        The selected page (index 1)
    *pages*
        The number of pages (index 1)
    Returns: A *(visible_pages , seperators)* tuple where both
    are lists.
    '''

    ### If we have < 11 pages we show all page links
    ### X X X O X X X X X X X
    if pages <= 11:
        return [range(1, pages + 1), []]

    ### if we have > 11 pages, we select which boxes and
    ### which seperators to show
    # Case: near the start. Show the pages up to 9, a seperator
    # and the last 1
    # X X X X O X X X X ... X
    if selected_page <= 7:
        return [range(1, 9 + 1) + [pages], [10]]
    # Case: near the end. Show the first two pages, the seperator
    # and the last 9
    # X ... X X X X X O X X X
    if (pages - selected_page) <= 7:
        return [[1] + range(pages - 8, pages + 1), [2]]
    # Case: somewhere within the long list
    # X ... X X X O X X X ... X
    return [[1] + range(selected_page - 3, selected_page + 3 + 1) +
            [pages], [2, pages]]


class PagerMixin(object):

    @property
    def offset(self):
        return (self.page - 1) * self.size

    @property
    def pages(self):
        return int(math.ceil(self.total_num_items() / float(self.size)))

    def here(self):
        '''
        backwarts compatibility. Use :meth:`render_pager`.
        '''
        return self.render_pager()

    def page_sizes(self):
        if self.initial_size <= self.total_num_items():
            return []
        page_sizes = []
        # offer page sizes: from the initial size to either half of the
        # total size or 5 x the initial size.
        sizes = range(self.initial_size,
                      min(self.total_num_items() + self.initial_size / 2,
                          (self.initial_size * 5)) + 1,
                      self.initial_size / 2)
        for size in sizes:
            page_sizes.append(
                {'class': 'selected' if size == self.size else '',
                 'url': self.build_url(size=size),
                 'size': size,
                 'last': False})

        if page_sizes:
            page_sizes[-1]['last'] = True
        return page_sizes

    def pages_items(self):

        visible_pages_, seperators = visible_pages(self.page, self.pages)

        items = []
        for number in xrange(1, self.pages + 1):
            if number in seperators:
                item = {'current': False,
                        'url': '',
                        'label': '...',
                        'class': '',
                        'seperator': True}
                items.append(item)

            item = {'current': self.page == number,
                    'url': self.build_url(page=number),
                    'label': str(number),
                    'class': 'hidden' if number not in visible_pages_ else '',
                    'seperator': False}
            items.append(item)

        return items

    def build_url(self, page=None, size=None, sort=None, facets=tuple(),
                  unselect_facets=tuple(), **kwargs):
        '''
        b/w compat
        '''
        query = MultiDict(request.params.items())
        query.update(kwargs)
        query["%s_page" % self.name] = page if page else 1
        query["%s_size" % self.name] = size if size else self.size
        query["%s_sort" % self.name] = sort if sort else self.selected_sort

        # sanitize the the query arguments
        query_items = ([(str(key), unicode(value).encode('utf-8')) for
                        (key, value) in query.items()])
        url_base = url.current(qualified=True)
        return url_base + "?" + urllib.urlencode(query_items)

    def to_dict(self):
        return self.items

    def render_pager(self):
        '''
        render the template for the pager (without facets)
        '''
        return render_def('/pager.html', 'namedpager', pager=self)

    def __len__(self):
        return self.total_num_items()


# --[ sql based NamedPager ]------------------------------------------------

class NamedPager(PagerMixin):
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

    def total_num_items(self):
        return len(self._items)


def instances(instances):
    return NamedPager('instances', instances, tiles.instance.row,
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest,
                             _("activity"): sorting.instance_activity,
                             _("alphabetically"): sorting.delegateable_label},
                      default_sort=sorting.instance_activity,
                      size=20)  # FIXME: hardcoded for enquetebeteiligung


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


def users(users, instance):
    activity_sorting = sorting.user_activity_factory(instance)
    sorts = {_("oldest"): sorting.entity_oldest,
             _("newest"): sorting.entity_newest,
             _("activity"): activity_sorting,
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


def polls(polls, default_sort=None, **kwargs):
    if default_sort is None:
        default_sort = sorting.polls_time
    return NamedPager('polls', polls, tiles.poll.row,
                    default_sort=default_sort, **kwargs)


class Sorts(object):
    '''
    Class to store sorting options in :class:`SolrPager`
    '''

    def __init__(self, sorts):
        self._sorts = sorts
        self._keys = [sort[0] for sort in sorts]
        self._values = [sort[1] for sort in sorts]

    def keys(self):
        return self._keys

    def values(self):
        return self._values


# --[ solr pager ]----------------------------------------------------------

class SolrIndexer(object):
    '''
    An indexer class to add information to the data
    which will be indexed in solr.
    '''

    @classmethod
    def add_data_to_index(cls, entity, data):
        '''
        Add data from/based on *entity* to *data* which will be
        indexed in solr. Add information to it *data* or modify
        it. You don't need to return it.

        *entity*
           An :class:`adhocracy.model.meta.Indexable` object.
        *data*
           The data that will be send to solr.

        Return *None*
        '''
        raise NotImplemented('has to be implemented in subclass')


marker = object()


class SolrFacet(SolrIndexer):
    """
    A Facet that can be used in searches.
    It's used like this:

    globally:
    >>> class SomeFacet(SolrFacet):
    ...     name = 'badge'
    ...     entity_type = Badge
    ...     title = u'Badge'

    Only in a thread:
    >>> some_facet = SomeFacet('mypager_prefix', request)
    >>> q = solr_query()
    >>> counts_query = q
    >>> # configure the query further
    >>> q, counts_query = some_facet.add_to_queries(q, counts_query)
    >>> response = q.execute()
    >>> counts_response = counts_response.execute()
    >>> some_facet.update(response, counts_response)
    >>> some_facet.items
    [...]
    """

    # overwrite in subclasses
    name = None
    entity_type = None
    title = None
    description = None
    solr_field = None
    show_empty = False
    show_current_empty = True
    template = '/pager.html'
    _response = None

    def __init__(self, param_prefix, request, **kwargs):
        # Translate the title and the description. We need to do that
        # during the request.
        self.title = self.title and _(self.title) or None
        self.description = self.description and _(self.description) or None
        self.param_prefix = param_prefix
        self.request = request
        self.request_key = "%s_facet" % param_prefix
        self.used = self._used(request)
        for (key, value) in kwargs.items():
            setattr(self, key, value)

    @property
    def response(self):
        if self._response is None:
            raise AssertionError('You have to .update() the facet first')
        return self._response

    @response.setter
    def response(self, response):
        self._response = response

    def add_to_queries(self, query, counts_query):
        '''
        Add the facet to the queries *query* and *counts_query*.
        The difference is that the *query* will be limited to facet values
        used in the the request.

        Returns: the modified queries as a (query, counts_query) tuple
        '''
        query = query.facet_by(self.solr_field)
        counts_query = counts_query.facet_by(self.solr_field)
        for value in self.used:
            query = query.query(**{self.solr_field: value})
        return query, counts_query

    def update(self, response, counts_response):
        '''
        Compute and update different attributes of the facet based
        on the solr *response* and the *base_query*.
        '''
        self.response = response
        self.counts_response = counts_response
        solr_field = self.solr_field

        # the counts in the current query which is limited to selected
        # facet values
        current_counts = response.facet_counts.facet_fields[solr_field]
        self.sorted_current_counts = sorted(current_counts,
                                            key=lambda(value, count): count,
                                            reverse=True)
        self.current_counts = dict(self.sorted_current_counts)

        # the counts in the current query which is limited to selected
        # facet values
        facet_counts = counts_response.facet_counts.facet_fields[solr_field]
        self.sorted_facet_counts = sorted(facet_counts,
                                          key=lambda(value, count): count,
                                          reverse=True)
        self.facet_counts = dict(self.sorted_facet_counts)

        self.facet_items = self._facet_items(self.sorted_facet_counts)
        self.current_items = self._current_items()

    # fixme: memoize
    def _facet_items(self, facet_counts):
        facet_items = []
        for (value, count) in facet_counts:
            facet_item = self._facet_item(value, count)
            if facet_item is not None:
                facet_items.append(facet_item)
        return self.sort_facet_items(facet_items)

    def _facet_item(self, value, count):
        '''
        Return an item dict for the facet *value*.
        *selected_values* is list of values used in the current
        query. count is the number of entries for this value in
        the current query results.
        '''
        item = self.get_item_data(value)
        if item is None:
            return None
        item['facet_count'] = count
        item['value'] = value
        return item

    def sort_facet_items(self, items):
        '''
        hook to sort the items facet specific. This is a
        generic that works with entities and sorts by entity title,
        name or id, or by facet_count. It is only sensible if all
        entities have the same attributes.
        '''
        def sort_key_getter(item):
            entity = item.get('entity', None)
            if entity:
                for attribute in ['title', 'name', 'id']:
                    value = getattr(entity, attribute, marker)
                    if value is not marker:
                        return value
            return item['facet_count'] * -1  # reverse sorting

        return sorted(items, key=sort_key_getter)

    def available(self):
        if not self.response:
            return False
        return bool(len(self.current_items))

    def _used(self, request):
        used = []
        for param in request.params.getall(self.request_key):
            facet, value = param.split(':')
            if facet == self.name and value not in used:
                used.append(value)
        return used

    def _current_items(self):
        '''
        Return a list of facets to display.
        '''
        display_facet_items = []
        for item in self.facet_items:
            item = item.copy()
            facet_value = item['value']
            item['current_count'] = self.current_counts[facet_value]

            if item['current_count'] == 0 and not (self.show_empty or
                                                   self.show_current_empty):
                continue
            if item['facet_count'] == 0 and not self.show_empty:
                continue

            item['disabled'] = (item['current_count'] == 0)
            # filter out by configuration:
            if item['current_count'] == 0 and not self.show_current_empty:
                # facets that are now empty, but may return results
                # if another facet value combination is selected
                continue
            if item['facet_count'] == 0 and not self.show_empty:
                # facets that are 0 in all possible result sets.
                continue

            values = self.used[:]
            selected = facet_value in self.used
            item['selected'] = selected
            if selected:
                values.remove(facet_value)
            else:
                values.append(facet_value)
            item['url'] = self.build_url(self.request, values)

            display_facet_items.append(item)

        return display_facet_items

    def get_item_data(self, value):
        '''
        hook to get the entity (or other relevant data) for a facet.
        *value* is the facet_value, item the item dict that will be
        stored and passed to the templates.

        This is a generic version that works with entity types that
        have a generic method "find", and a displayable title
        stored in the attribute label, title or name.

        Raises ValueError if the displayable title cannot be found.

        Returns: An item dict or None if no data can be found for
        the *value*
        '''
        entity = self.entity_type.find(value)
        if entity is None:
            return None
        item = {}
        item['entity'] = entity
        # find an link_text
        for attribute in ['label', 'title', 'name']:
            if hasattr(entity, attribute):
                item['link_text'] = getattr(entity, attribute)
                return item
        raise ValueError('Could not find a link_text for %s' % entity)

    def unselect_all_link(self):
        '''
        return an url where no value for this facet is selected
        '''
        return self.build_url(self.request, [])

    def build_url(self, request, facet_values):
        '''
        Build an url from the *request* and the *facet_value*
        '''
        params = self.build_params(request, facet_values)
        url_base = url.current(qualified=True)
        return url_base + "?" + urllib.urlencode(params)

    def build_params(self, request, facet_values):
        '''
        Build query parameters using the facet_values for this facet
        and the request.

        Returns: a list of (parameter, value) two-tuples
        '''
        params = MultiDict(request.params)

        # removing all ..._facet parameters and add them again
        current_facet_parameters = params.getall(self.request_key)
        if self.request_key in params:
            del params[self.request_key]

        # readd all _facet parameters not related to us
        for parameter in current_facet_parameters:
            name, value = parameter.split(':')
            if name != self.name:
                params.add(self.request_key, parameter)

        # add parameters for our facets
        facet_values = list(set(facet_values))
        for value in facet_values:
            params.add(self.request_key, "%s:%s" % (self.name, value))

        # sanitize and encode
        items = ([(str(key), unicode(value).encode('utf-8')) for
                  (key, value) in params.items()])
        return items

    def render(self):
        return render_def(self.template, 'facet', facet=self)


class UserBadgeFacet(SolrFacet):

    name = 'userbadge'
    entity_type = model.Badge
    title = u'Badge'
    solr_field = 'facet.badges'

    @classmethod
    def add_data_to_index(cls, user, index):
        if not isinstance(user, model.User):
            return
        index[cls.solr_field] = [badge.id for badge in user.badges]


class InstanceFacet(SolrFacet):

    name = 'instance'
    entity_type = model.Instance
    title = u'Projektgruppe'
    solr_field = 'facet.instances'

    @classmethod
    def add_data_to_index(cls, user, index):
        if not isinstance(user, model.User):
            return
        index[cls.solr_field] = [instance.key for instance in user.instances]


class DelegateableBadgeFacet(SolrFacet):

    name = 'delegateablebadge'
    entity_type = model.Badge
    title = u'Beteiligte'  # FIXME: translate
    solr_field = 'facet.delegateable.badge'

    @classmethod
    def add_data_to_index(cls, entity, data):
        if not isinstance(entity, model.Delegateable):
            return
        data[cls.solr_field] = [badge.id for badge in
                                entity.delegateablebadges]


class DelegateableAddedByBadgeFacet(SolrFacet):

    name = 'added_by_badge'
    entity_type = model.Badge
    title = u'Erstellt von'  # FIXME: translate
    solr_field = 'facet.delegateable.added.by.badge'

    @classmethod
    def add_data_to_index(cls, entity, data):
        if not isinstance(entity, model.Delegateable):
            return
        data[cls.solr_field] = [badge.id for badge in entity.creator.badges]


class CommentOrderIndexer(SolrIndexer):

    solr_field = 'order.comment.order'

    @classmethod
    def add_data_to_index(cls, entity, data):
        if isinstance(entity, model.Comment):
            data[cls.solr_field] = sorting.comment_order_key(entity)


class CommentScoreIndexer(SolrIndexer):

    solr_field = 'order.comment.score'

    @classmethod
    def add_data_to_index(cls, entity, data):
        if isinstance(entity, model.Comment):
            data[cls.solr_field] = entity.poll.tally.score


class NormNumSelectionsIndexer(SolrIndexer):

    solr_field = 'order.norm.num_selections'

    @classmethod
    def add_data_to_index(cls, entity, data):
        if (isinstance(entity, model.Page) and
            entity.function == model.Page.NORM):
            data[cls.solr_field] = len(entity.selections)


class NormNumVariantsIndexer(SolrIndexer):

    solr_field = 'order.norm.selections'

    @classmethod
    def add_data_to_index(cls, entity, data):
        if (isinstance(entity, model.Page) and
            entity.function == model.Page.NORM):
            data[cls.solr_field] = len(entity.selections)


class ProposalSupportIndexer(SolrIndexer):

    solr_field = 'order.proposal.support'

    @classmethod
    def add_data_to_index(cls, entity, data):
        if isinstance(entity, model.Proposal):
            data[cls.solr_field] = entity.rate_poll.tally.num_for


class ProposalMixedIndexer(SolrIndexer):

    solr_field = 'order.proposal.mixed'

    @classmethod
    def add_data_to_index(cls, entity, data):
        if isinstance(entity, model.Proposal):
            data[cls.solr_field] = sorting.proposal_mixed_key(entity)


class UserActivityIndexer(SolrIndexer):

    @classmethod
    def solr_field(cls, instance=None):
        field = 'order.user.activity'
        if instance is not None:
            field = field + '.%s' % instance.key
        return field

    @classmethod
    def add_data_to_index(cls, entity, data):
        if isinstance(entity, model.User):
            activity_sum = 0
            for instance in entity.instances:
                activity = user_activity(instance, entity)
                data[cls.solr_field(instance)] = activity
                activity_sum = activity_sum + activity
            data[cls.solr_field()] = activity_sum


INDEX_DATA_FINDERS = [UserBadgeFacet, InstanceFacet,
                      CommentOrderIndexer, CommentScoreIndexer,
                      DelegateableAddedByBadgeFacet, DelegateableBadgeFacet,
                      NormNumSelectionsIndexer, NormNumSelectionsIndexer,
                      ProposalSupportIndexer, ProposalMixedIndexer,
                      UserActivityIndexer]


class SolrPager(PagerMixin):
    '''
    An pager currently compatible to :class:`adhocracy.lib.pager.NamedPager`.
    '''

    def __init__(self, name, itemfunc, entity_type=None, extra_filter=None,
                 initial_size=20, size=None, sorts=tuple(), default_sort=None,
                 enable_sorts=True, enable_pages=True, facets=tuple(),
                 wildcard_queries=None):
        self.name = name
        self.itemfunc = itemfunc
        self.enable_pages = enable_pages
        self.enable_sorts = enable_sorts
        self.extra_filter = extra_filter
        self.facets = [Facet(self.name, request) for Facet in facets]
        self.wildcard_queries = wildcard_queries or {}
        self.initial_size = initial_size
        if size is not None:
            self.size = size
        elif c.user and c.user.page_size:
            self.size = c.user.page_size
        else:
            self.size = initial_size
        self.size = self._get_size()

        self.sorts = Sorts(sorts)
        self.default_sort = default_sort
        if len(self.sorts.values()) and self.default_sort:
            self.selected_sort = self.sorts.values().index(default_sort) + 1
        else:
            self.selected_sort = 1
        self.selected_sort = self._get_sort()

        self.page = self._get_page()

        ## build the query
        query = sunburnt_query(entity_type)
        if self.extra_filter:
            query = query.filter(**self.extra_filter)
        for field, string in self.wildcard_queries.items():
            query = add_wildcard_query(query, field, string)

        # Add facets
        counts_query = query
        counts_query = counts_query.paginate(rows=0)

        for facet in self.facets:
            query, counts_query = facet.add_to_queries(query, counts_query)

        # Add pagination and sorting
        if enable_pages:
            query = query.paginate(start=self.offset, rows=self.size)
        if self.sorts.keys():
            sort_by = self.sorts.values()[self.selected_sort - 1]
            query = query.sort_by(sort_by)

        # query solr and calculate values from it
        self.response = query.execute()
        self.counts_response = counts_query.execute()

        # if we are out of the page range do a permanent redirect
        # to the last page
        if (self.pages > 0) and (self.page > self.pages):
            new_url = self.build_url(page=self.pages)
            redirect(new_url, code=301)

        for facet in self.facets:
            facet.update(self.response, self.counts_response)
        self.items = self._items_from_response(self.response)

    def total_num_items(self):
        '''
        return the total numbers of results
        '''
        return self.response.result.numFound

    def _items_from_response(self, response):
        '''
        Get model objects form the documents returned
        in the solr *response*.
        '''
        items = []
        if not response.result.numFound:
            return items

        # Don't use entity_type.find_all() cause
        # it won't preserve the order of items.
        entities = []
        for doc in response.result.docs:
            ref = doc.get('ref')
            entity = model.refs.to_entity(ref)
            entities.append(entity)
        return entities

    def _get_page(self):
        page = 1
        try:
            page_value = request.params.get("%s_page" % self.name)
            page = PAGE_VALIDATOR.to_python(page_value)
        finally:
            return page

    def _get_size(self):

        size = self.size
        try:
            size_value = request.params.get("%s_size" % self.name)
            size = SIZE_VALIDATOR.to_python(size_value)
        finally:
            return size

    def _get_sort(self):
        sort = request.params.get("%s_sort" % self.name)
        if sort is None:
            return self.selected_sort
        else:
            return int(sort)

    def render_facets(self):
        '''
        render all facets
        '''
        return render_def('/pager.html', 'facets', pager=self)


def solr_instance_users_pager(instance):
    extra_filter = {'facet.instances': instance.key}
    activity_sort_field = '-activity.%s' % instance.key
    pager = SolrPager('users', tiles.user.row,
                      entity_type=model.User,
                      sorts=((_("oldest"), '+create_time'),
                             (_("newest"), '-create_time'),
                             (_("activity"), activity_sort_field),
                             (_("alphabetically"), 'order.title')),
                      extra_filter=extra_filter,
                      default_sort=activity_sort_field,
                      facets=[UserBadgeFacet])
    return pager


def solr_global_users_pager():
    activity_sort_field = '-activity'
    pager = SolrPager('users', tiles.user.row,
                      entity_type=model.User,
                      sorts=((_("oldest"), '+create_time'),
                             (_("newest"), '-create_time'),
                             (_("activity"), activity_sort_field),
                             (_("alphabetically"), 'order.title')),
                      default_sort=activity_sort_field,
                      facets=[UserBadgeFacet, InstanceFacet]
                      )
    return pager


def solr_proposal_pager(instance, wildcard_queries=None):
    extra_filter = {'instance': instance.key}
    support_sort_field = '-order.proposal.support'
    pager = SolrPager('proposals', tiles.proposal.row,
                      entity_type=model.Proposal,
                      sorts=((_("newest"), '-create_time'),
                             (_("support"), support_sort_field),
                             (_("mixed"), '-order.proposal.mixed'),
                             (_("alphabetically"), 'order.title')),
                      default_sort=support_sort_field,
                      extra_filter=extra_filter,
                      facets=[DelegateableBadgeFacet,
                              DelegateableAddedByBadgeFacet],
                      wildcard_queries=wildcard_queries)
    return pager
