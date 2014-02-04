#!/usr/bin/env python

from adhocracy.tests import TestController


class TestEntityUrl(TestController):
    """ at the moment these tests are limited only to those cases
    which are interesting for #607. """

    def _make_content(self):
        """Returns instance and user"""

        from adhocracy import model

        instance = model.Instance.find(u'test')
        user = model.User.create(u'user', u'user@mail.com')

        return instance, user

    def test_page_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        page = model.Page.create(instance, u'test_page', u'text', user)
        url = u'http://test.test.lan/page/test_page'

        self.assertEqual(entity_url(page), url)

    def test_page_edit_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        page = model.Page.create(instance, u'test_page', u'text', user)
        url = u'http://test.test.lan/page/test_page/edit'

        self.assertEqual(entity_url(page, member=u'edit'), url)

    def test_subpage_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        parent = model.Page.create(instance, u'test_parent', u'text', user)
        page = model.Page.create(instance, u'test_page', u'text', user)
        page.parents.append(parent)
        url = u'http://test.test.lan/page/test_page'

        self.assertEqual(entity_url(page), url)

    def test_subpage_edit_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        parent = model.Page.create(instance, u'test_parent', u'text', user)
        page = model.Page.create(instance, u'test_page', u'text', user)
        page.parents.append(parent)
        url = u'http://test.test.lan/page/test_page/edit'

        self.assertEqual(entity_url(page, member=u'edit'), url)

    def test_proposal_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        proposal = model.Proposal.create(instance, u'test_proposal', user)
        url = u'http://test.test.lan/proposal/%i-test_proposal' % proposal.id

        self.assertEqual(entity_url(proposal), url)

    def test_proposal_edit_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        proposal = model.Proposal.create(instance, u'test_proposal', user)
        url = u'http://test.test.lan/proposal/%i-test_proposal/edit' % (
            proposal.id)

        self.assertEqual(entity_url(proposal, member=u'edit'), url)

    def test_proposal_comment_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        proposal = model.Proposal.create(instance, u'test_proposal', user)
        comment = model.Comment.create(u'text', user, proposal)
        url = u'http://test.test.lan/proposal/%i-test_proposal#c%i' % (
            proposal.id, comment.id)

        self.assertEqual(entity_url(comment), url)

    def test_sectionpage_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        page = model.Page.create(instance, u'test_page', u'text', user,
                                 sectionpage=True)
        url = u'http://test.test.lan/page/test_page'

        self.assertEqual(entity_url(page), url)

    def test_sectionpage_edit_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        page = model.Page.create(instance, u'test_page', u'text', user,
                                 sectionpage=True)
        url = u'http://test.test.lan/page/test_page/edit'

        self.assertEqual(entity_url(page, member='edit'), url)

    def test_sectionpage_subpage_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        parent = model.Page.create(instance, u'test_parent', u'text', user,
                                   sectionpage=True)
        page = model.Page.create(instance, u'test_page', u'text', user)
        page.parents.append(parent)
        url = u'http://test.test.lan/page/test_parent#subpage-%i' % page.id

        self.assertEqual(entity_url(page), url)

    def test_sectionpage_subpage_edit_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        parent = model.Page.create(instance, u'test_parent', u'text', user,
                                   sectionpage=True)
        page = model.Page.create(instance, u'test_page', u'text', user)
        page.parents.append(parent)
        url = u'http://test.test.lan/page/test_page/edit'

        self.assertEqual(entity_url(page, member=u'edit'), url)

    def test_amendment_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        page = model.Page.create(instance, u'test_page', u'text', user,
                                 sectionpage=True)
        proposal = model.Proposal.create(instance, u'test_proposal', user,
                                         is_amendment=True)
        _selection = model.Selection.create(proposal, page, user)
        url = u'http://test.test.lan/page/test_page?overlay_type=' \
            u'%23overlay-url-big&overlay_path=http%3A%2F%2Ftest.test.lan' \
            u'%2Fpage%2Ftest_page%2Famendment%2F{0}.overlay' \
            .format(proposal.id)

        self.assertEqual(entity_url(proposal), url)

    def test_amendment_edit_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        page = model.Page.create(instance, u'test_page', u'text', user,
                                 sectionpage=True)
        proposal = model.Proposal.create(instance, u'test_proposal', user,
                                         is_amendment=True)
        _selection = model.Selection.create(proposal, page, user)
        url = u'http://test.test.lan/proposal/%i-test_proposal/edit' % (
            proposal.id)

        self.assertEqual(entity_url(proposal, member=u'edit'), url)

    def test_sectionpage_comment_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        instance, user = self._make_content()

        page = model.Page.create(instance, u'test_page', u'text', user,
                                 sectionpage=True)
        comment = model.Comment.create(u'text', user, page)
        url = u'http://test.test.lan/page/test_page?overlay_type=' \
            u'%23overlay-url&overlay_path=http%3A%2F%2Ftest.test.lan%2Fpage' \
            u'%2Ftest_page%2Fcomments.overlay%23c{0}' \
            .format(comment.id)

        self.assertEqual(entity_url(comment), url)

    def test_sectionpage_subpage_comment_entity_url(self):
        from adhocracy.lib.helpers import entity_url
        from adhocracy import model

        self.maxDiff = None

        instance, user = self._make_content()

        parent = model.Page.create(instance, u'test_parent', u'text', user,
                                   sectionpage=True)
        page = model.Page.create(instance, u'test_page', u'text', user)
        page.parents.append(parent)
        comment = model.Comment.create(u'text', user, page)
        url = u'http://test.test.lan/page/test_parent?overlay_type=' \
            u'%23overlay-url&overlay_path=http%3A%2F%2Ftest.test.lan%2Fpage' \
            u'%2Ftest_page%2Fcomments.overlay%23c{0}' \
            .format(comment.id, page.id)

        self.assertEqual(entity_url(comment), url)
