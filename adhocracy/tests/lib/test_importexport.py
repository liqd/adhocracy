
import contextlib
import io
import zipfile

import adhocracy.lib.importexport as importexport
from adhocracy.tests import TestController
import adhocracy.tests.testtools as testtools
from adhocracy import model

class _MockResponse(object):
    pass

try:
    _compat_str = unicode
except NameError:
    _compat_str = str


class ImportExportTest(TestController):
    def setUp(self):
        super(ImportExportTest, self).setUp()
        self.u1 = testtools.tt_make_user()
        self.u2 = testtools.tt_make_user()
        self.instance = testtools.tt_make_instance(u'export_test', label=u'export_test', creator=self.u2)

    def test_transforms(self):
        tfs = importexport.transforms.gen_all({})
        self.assertTrue(any(tf.name.lower() == u'user' for tf in tfs))

        tfs = importexport.transforms.gen_active({})
        self.assertEquals(len(tfs), 0)


    def test_export_basic(self):
        e = importexport.export_data({})
        self.assertEquals(len(e), 1)
        self.assertEquals(e['metadata']['type'], 'normsetting-export')
        self.assertTrue(e['metadata']['version'] >= 3)

    def test_export_user(self):
        e = importexport.export_data(dict(include_user=True, user_personal=True, user_password=True))
        users = e['user']
        self.assertTrue(len(users) >= 2)
        self.assertTrue(any(u['user_name'] == self.u1.user_name for u in users.values()))
        self.assertTrue(any(u['email'] == self.u2.email for u in users.values()))
        self.assertTrue(any(u['adhocracy_password'] == self.u1.password for u in users.values()))
        self.assertTrue(all(u'_' in u['locale'] for u in users.values()))
        assert len(users) == len(model.User.all())

    def test_export_anonymous(self):
        e = importexport.export_data(dict(include_user=True))
        users = e['user']
        self.assertTrue(len(users) >= 2)
        self.assertTrue(all(len(u) == 0 for u in users.values()))
        self.assertTrue(not any(self.u1.user_name in k for k in users.keys()))

    def test_export_instance(self):
        ed = importexport.export_data(dict(include_instance=True,
                                         include_user=True, user_personal=True))
        # Test that we don't spill non-representable objects by accident
        ex = importexport.formats.render(ed, 'json', '(title)', response=_MockResponse())
        e = importexport.formats.read_data(io.BytesIO(ex))

        self.assertTrue('instance' in e)
        self.assertTrue(len(e['instance']) >= 1)
        self.assertTrue(self.instance.key in e['instance'])
        idata = e['instance'][self.instance.key]
        self.assertEquals(idata['label'], self.instance.label)
        self.assertEquals(idata['key'], self.instance.key)

        user_id = idata['creator']
        assert user_id
        self.assertTrue(isinstance(user_id, _compat_str))
        self.assertEquals(e['user'][user_id]['user_name'], self.u2.user_name)
        self.assertEquals(idata['adhocracy_type'], 'instance')

    def test_export_proposal(self):
        p = testtools.tt_make_proposal(creator=self.u1)
        e = importexport.export_data({
            "include_instance": True,
            "include_instance_proposals": True,
            "include_users": True,
        })
        idata = e['instance'][p.instance.key]
        self.assertTrue('proposals' in idata)
        pdata = idata['proposals'][str(p.id)]
        assert 'comments' not in pdata 
        self.assertEquals(pdata['title'], p.title)
        self.assertEquals(pdata['description'], p.description)
        self.assertEquals(pdata['adhocracy_type'], 'proposal')

    def test_export_comments(self):
        p = testtools.tt_make_proposal(creator=self.u1, with_description=True)
        desc = testtools.tt_make_str()
        c1 = model.Comment.create(
            text=desc,
            user=self.u2,
            topic=p.description,
            reply=None,
            variant='HEAD',
            sentiment=1)
        assert p.description.comments
        e = importexport.export_data({
            "include_instance": True,
            "include_instance_proposals": True,
            "include_instance_proposal_comments": True,
            "include_users": True,
        })
        idata = e['instance'][p.instance.key]
        pdata = idata['proposals'][str(p.id)]
        assert 'comments' in pdata
        self.assertEquals(len(pdata['comments']), 1)
        cdata = next(iter(pdata['comments'].values()))
        self.assertEquals(cdata['text'], desc)
        self.assertEquals(cdata['creator'], str(self.u2.id))
        self.assertEquals(cdata['sentiment'], 1)
        self.assertEquals(cdata['adhocracy_type'], 'comment')


    def test_rendering(self):
        e = importexport.export_data(dict(include_user=True, user_personal=True,
            user_password=True, include_badge=True))
        self.assertEquals(set(e.keys()), set(['metadata', 'user', 'badge']))

        formats = importexport.formats

        response = _MockResponse()
        zdata = formats.render(e, 'zip', 'test', response=response)
        with contextlib.closing(zipfile.ZipFile(io.BytesIO(zdata), 'r')) as zf:
            self.assertEquals(set(zf.namelist()), set(['metadata.json', 'user.json', 'badge.json']))
        zio = io.BytesIO(zdata)
        self.assertEquals(formats.detect_format(zio), 'zip')
        self.assertEquals(zio.read(), zdata)
        self.assertEquals(e, formats.read_data(io.BytesIO(zdata), 'zip'))
        self.assertEquals(e, formats.read_data(io.BytesIO(zdata), 'auto'))

        response = _MockResponse()
        jdata = formats.render(e, 'json', 'test', response=response)
        response = _MockResponse()
        jdata_dl = formats.render(e, 'json_download', 'test', response=response)
        self.assertEquals(jdata, jdata_dl)
        self.assertTrue(isinstance(jdata, bytes))
        jio = io.BytesIO(jdata)
        self.assertEquals(formats.detect_format(jio), 'json')
        self.assertEquals(jio.read(), jdata)
        self.assertEquals(e, formats.read_data(io.BytesIO(jdata), 'json'))
        self.assertEquals(e, formats.read_data(io.BytesIO(jdata), 'auto'))

        self.assertRaises(ValueError, formats.render, e, 'invalid', 'test', response=response)
        self.assertRaises(ValueError, formats.read_data, zdata, 'invalid')

