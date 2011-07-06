from copy import deepcopy
import urllib
import math
import logging

from formencode import validators
from pylons.i18n import _
from pylons import request, tmpl_context as c, url
from pylons.controllers.util import redirect
from webob.multidict import MultiDict

from adhocracy.lib.templating import render_def
from adhocracy.lib import sorting, tiles
from adhocracy.lib.search.query import sunburnt_query
from adhocracy.model import refs, User, Badge

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


marker = object()

class SolrFacet(object):
    """
    A Facet that can be used in searches.
    It's used like this:

    globally:
    >>> SomeFacet = Facet('badge', Badge, u'Badge')
    >>> some_facet.solr_field
    facet.badge

    Only in a thread:
    >>> some_facet = SorlFacet('mypager_prefix', request)
    >>> q = solr_query()
    >>> # configure the query further
    >>> q = some_facet.add_to_query(q)
    >>> response = q.execute()
    >>> some_facet.update(response)
    >>> some_facet.items
    [...]
    """
    def __init__(self, name, entity_type, title, description=None,
                 tile=None, solr_field=None):
        self.name = name
        self.entity_type = entity_type
        self.title = title
        self.description = description
        self.tile = tile
        self.solr_field = solr_field or "facet." + name

    def update(self, response):
        self.response = response
        counts = response.facet_counts.facet_fields[self.solr_field]
        self.sorted_counts = sorted(counts, key=lambda(value, count): count,
                                    reverse=True)
        self.counts = dict(self.sorted_counts)
        self.items = self._items(self.used, self.sorted_counts)

    def _used(self, request):
        used = []
        for param in request.params.getall(self.request_key):
            facet, value = param.split(':')
            if facet == self.name and value not in used:
                used.append(value)
        return used

    def sort_items(self, items):
        '''
        hook to sort the items facet specific
        '''
        def sort_key_getter(item):
            entity = item.get('entity', None)
            if entity:
                for attribute in ['title', 'name', 'id']:
                    value = getattr(entity, attribute, marker)
                    if value is not marker:
                        return value
            return item['count'] * -1  # reverse sorting

        return sorted(items, key=sort_key_getter)

    def _items(self, used, value_counts):
        items = []
        for (value, count) in value_counts:
            item = self._item(used, value, count)
            if item is not None:
                items.append(item)

        return self.sort_items(items)

    def _item(self, values, value, count):
        '''
        fixme: this is hard coded to use badges for now.
        '''

        entity = self.entity_type.by_id(value)
        if entity is None:
            log.debug('missed entiy "%s" for entity class "%s"' % (
                value, self.entity_type))
            return None
        values = values[:]
        selected = value in values
        if selected and value in values:
            values.remove(value)
        if not selected:
            values.append(value)

        item = {'url': self.build_url(self.request, values),
                'selected': selected,
                'count': count,
                'entity': entity}
        return item

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

    def __call__(self, param_prefix, request):
        description = self.description and _(self.description) or None
        facet = self.__class__(self.name, self.entity_type, _(self.title),
                               description=description, tile=self.tile,
                               solr_field=self.solr_field)
        facet.param_prefix = param_prefix
        facet.request = request
        facet.request_key = "%s_facet" % param_prefix
        facet.used = facet._used(request)
        return facet

    def render(self):
        return render_def('/pager.html', 'facet', facet=self)

    def add_to_query(self, q):
        q = q.facet_by(self.solr_field)
        for value in self.used:
            q = q.query(**{self.solr_field: value})
        return q

BadgeFacet = SolrFacet('badge', Badge, u'Badge', solr_field='badges')


class SolrPager(object):
    '''
    An pager currently compatible to :class:`adhocracy.lib.pager.NamedPager`.
    The API will not stay compatible and will be refactored
    in the future.
    '''

    def __init__(self, name, itemfunc, entity_type=None, extra_filter=None,
                 initial_size=20, size=None, sorts=tuple(), default_sort=None,
                 enable_sorts=True, enable_pages=True, facets=tuple()):
        self.name = name
        self.itemfunc = itemfunc
        self.enable_pages = enable_pages
        self.enable_sorts = enable_sorts
        self.extra_filter = extra_filter
        self.facets = [Facet(self.name, request) for Facet in facets]
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
        self.offset = (self.page - 1) * self.size

        self.base_query = sunburnt_query(entity_type)
        q = self.base_query
        if enable_pages:
            q = q.paginate(start=self.offset, rows=self.size)
        if self.extra_filter:
            q = q.filter(**self.extra_filter)
        if self.sorts.keys():
            sort_by = self.sorts.values()[self.selected_sort - 1]
            q = q.sort_by(sort_by)

        for facet in self.facets:
            q = facet.add_to_query(q)
        self.response = q.execute()
        self.pages = int(math.ceil(self.response.result.numFound /
                                   float(self.size)))

        # if we are out of the page range do a permanent redirect
        # to the last page
        if (self.pages > 0) and (self.page > self.pages):
            new_url = self.serialize(page=self.pages)
            redirect(new_url, code=301)

        for facet in self.facets:
            facet.update(self.response)
        self._items = self._items_from_response(self.response)

    @property
    def items(self):
        '''
        bw compat
        '''
        return self._items

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
            entity = refs.to_entity(ref)
            entities.append(entity)
        return entities

    def _get_page(self):
        page = 1
        try:
            page_value = request.params.get("%s_page" % self.name)
            page = PAGE_VALIDATOR.to_python(page_value)
        finally:
            return page

    def serialize(self, page=None, size=None, sort=None, facets=tuple(),
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

    def render_pager(self):
        '''
        render the template for the pager (without facets)
        '''
        return render_def('/pager.html', 'namedpager', pager=self)
        
    def render_facets(self):
        '''
        render all facets
        '''
        return render_def('/pager.html', 'facets', pager=self)


def solr_instance_users_pager(instance):
    extra_filter = {'instances': instance.key}
    activity_sort_field = '-activity.%s' % instance.key
    pager = SolrPager('users', tiles.user.row,
                      entity_type=User,
                      sorts=((_("oldest"), '+create_time'),
                             (_("newest"), '-create_time'),
                             (_("activity"), activity_sort_field),
                             (_("alphabetically"), 'sort_title')),
                      extra_filter=extra_filter,
                      default_sort=activity_sort_field,
                      facets=[BadgeFacet])
    return pager


def solr_global_users_pager():
    activity_sort_field = '-activity'
    pager = SolrPager('users', tiles.user.row,
                      entity_type=User,
                      sorts=((_("oldest"), '+create_time'),
                             (_("newest"), '-create_time'),
                             (_("activity"), activity_sort_field),
                             (_("alphabetically"), 'sort_title')),
                      default_sort=activity_sort_field,
                      facets=[BadgeFacet]
                      )
    return pager
