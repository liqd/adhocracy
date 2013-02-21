from unittest import TestCase
from StringIO import StringIO

from sunburnt.schema import SolrSchema
from sunburnt.search import SolrSearch


# borrowed from sunburnt.test_search
schema_string = \
    """<schema name="timetric" version="1.1">
      <types>
        <fieldType name="string" class="solr.StrField" sortMissingLast="true"
                   omitNorms="true"/>
      </types>
      <fields>
        <field name="text" required="true" type="string" multiValued="true"/>
      </fields>
      <defaultSearchField>text</defaultSearchField>
    </schema>
    """

schema = SolrSchema(StringIO(schema_string))


class MockInterface(object):
    schema = schema

interface = MockInterface


class TestSolrSearch(TestCase):

    def test_wildcard_search(self):
        from adhocracy.lib.search.query import add_wildcard_query
        search = SolrSearch(interface)
        query = add_wildcard_query(search, 'text', 'one two')
        self.assertEqual(
            query.params(),
            [('q', '(text:one OR text:one*) AND (text:two OR text:two*)')])

    def test_wildcard_search_cleaned_up(self):
        from adhocracy.lib.search.query import add_wildcard_query
        search = SolrSearch(interface)
        query = add_wildcard_query(search, 'text', 'one** two*')
        self.assertEqual(
            query.params(),
            [('q', '(text:one OR text:one*) AND (text:two OR text:two*)')])

    def test_wildcard_search_added_to_search(self):
        from adhocracy.lib.search.query import add_wildcard_query
        search = SolrSearch(interface).query(text='passedin')

        query = add_wildcard_query(search, 'text', 'wild')
        self.assertEqual(
            query.params(),
            [('q', 'text:passedin AND (text:wild OR text:wild*)')])

    def test_wildcard_search_ignore_none(self):
        from adhocracy.lib.search.query import add_wildcard_query
        search = SolrSearch(interface)

        query = add_wildcard_query(search, 'text', None)
        self.assertEqual(
            query.params(),
            [('q', '*:*')])
