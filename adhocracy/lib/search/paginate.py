import math
from urllib import urlencode

from formencode import validators
from pylons import request, tmpl_context as c

from adhocracy.model import refs
from adhocracy.lib.search.query import sunburnt_query
from adhocracy.lib.templating import render_def

PAGE_VALIDATOR = validators.Int(min=1, not_empty=True)
SIZE_VALIDATOR = validators.Int(min=1, max=250, not_empty=True)


class Sorts(object):

    def __init__(self, sorts):
        self._sorts = sorts
        self._keys = [sort[0] for sort in sorts]
        self._values = [sort[1] for sort in sorts]

    def keys(self):
        return self._keys

    def values(self):
        return self._values


class SolrPager(object):
    '''
    An pager currently compatible to :class:`adhocracy.lib.pager.NamedPager`.
    The API will not stay compatible and will be refactored
    in the future.
    '''

    def __init__(self, name, itemfunc, entity_type=None, extra_filter=None,
                 initial_size=20, size=None, sorts=tuple(), default_sort=None,
                 enable_sorts=True, enable_pages=True, **kwargs):
        self.name = name
        self.entity_type = entity_type
        self.itemfunc = itemfunc
        self.enable_pages = enable_pages
        self.extra_filter = extra_filter
        self.initial_size = initial_size
        if size is not None:
            self.size = size
        elif c.user and c.user.page_size:
            self.size = c.user.page_size
        else:
            self.size = initial_size
        self.size = self._get_size()

        self.sorts = Sorts(sorts)
        if len(self.sorts.values()):
            self.selected_sort = sorts.values().index(default_sort) + 1
        else:
            self.selected_sort = 0

        self.page = self._get_page()
        self.offset = (self.page - 1) * self.size
        self.sort = self._get_sort()

        self.base_query = sunburnt_query(entity_type)
        q = self.base_query
        if enable_pages:
            q = q.paginate(start=self.offset, rows=self.size)
        if self.extra_filter:
            q.filter(**self.extra_filter)
        if self.sorts.keys():
            q = q.sort_by(self.sort.values()[self.selected_sort])
        self.response = q.execute()
        self._items = self._items_from_response(self.response)
        self.pages = int(math.ceil(len(self._items) / float(self.size)))

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

        if (self.entity_type is not None and
            hasattr(self.entity_type, 'find_all')):
            ids = [refs.to_id(r.get('ref')) for r in response.result.docs]
            return self.entity_type.find_all(ids)

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

    def serialize(self, page=None, size=None, sort=None, **kwargs):
        '''
        b/w compat
        '''
        query = dict(request.params.items())
        query.update(kwargs)
        query["%s_page" % self.name] = page if page else 1
        query["%s_size" % self.name] = size if size else self.size
        query["%s_sort" % self.name] = sort if sort else self.selected_sort

        query = dict([(str(k), unicode(v).encode('utf-8')) \
                      for k, v in query.items()])
        return "?" + urlencode(query.items())

    def _get_size(self):

        size = self.size
        try:
            size_value = request.params.get("%s_size" % self.name)
            size = SIZE_VALIDATOR.to_python(size_value)
        finally:
            return size

    def _get_sort(self):
        sort = request.params.get("%s_sort" % self.name)
        return sort

    def here(self):
        '''
        b/w compat
        '''
        return render_def('/pager.html', 'namedpager', pager=self)
