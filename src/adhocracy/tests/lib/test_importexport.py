
import contextlib
import io
import zipfile

import adhocracy.lib.importexport as importexport
from adhocracy.tests import TestController
import adhocracy.tests.testtools as testtools
from adhocracy import model

class _MockResponse(object):
    pass

class ImportExportTest(TestController):
    def setUp(self):
        super(ImportExportTest, self).setUp()
        self.u1 = testtools.tt_make_user()
        self.u1.gender = 'f'
        self.badge = model.UserBadge.create(
            title=u'importexport_badge',
            color=u'#ff00ff',
            visible=True,
            description=u'This badge tests',
        )
        self.u2 = testtools.tt_make_user()
        self.badge.assign(user=self.u1, creator=self.u2)
        self.instance = testtools.tt_make_instance(u'export_test', label=u'export_test', creator=self.u2)

    def test_transforms(self):
        tfs = importexport.transforms.gen_all({})
        self.assertTrue(any(tf.name.lower() == u'user' for tf in tfs))

        tfs = importexport.transforms.gen_active({})
        self.assertEqual(len(tfs), 0)


    def test_export_basic(self):
        e = importexport.export_data({})
        self.assertEqual(len(e), 1)
        self.assertEqual(e['metadata']['type'], 'normsetting-export')
        self.assertTrue(e['metadata']['version'] >= 3)

    def test_export_user(self):
        e = importexport.export_data(dict(include_user=True, user_personal=True, user_password=True))
        users = e['user'].values()
        self.assertTrue(len(users) >= 2)
        self.assertTrue(any(u['user_name'] == self.u1.user_name for u in users))
        self.assertTrue(any(u['email'] == self.u2.email for u in users))
        self.assertTrue(any(u['adhocracy_password'] == self.u1.password for u in users))
        self.assertTrue(all(u'_' in u['locale'] for u in users))
        u1 = next(u for u in users if u['email'] == self.u1.email)
        self.assertEqual(u1['gender'], 'f')
        assert len(users) == len(model.User.all())

    def test_export_anonymous(self):
        e = importexport.export_data(dict(include_user=True))
        users = e['user']
        self.assertTrue(len(users) >= 2)
        self.assertTrue(all(len(u) == 0 for u in users.values()))
        self.assertTrue(not any(self.u1.user_name in k for k in users.keys()))
        u1 = next(iter(users))
        self.assertTrue('gender' not in u1)

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
        self.assertEqual(idata['label'], self.instance.label)
        self.assertEqual(idata['key'], self.instance.key)

        user_id = idata['creator']
        assert user_id
        self.assertTrue(isinstance(user_id, (str, unicode)))
        self.assertEqual(e['user'][user_id]['user_name'], self.u2.user_name)
        self.assertEqual(idata['adhocracy_type'], 'instance')

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
        self.assertEqual(pdata['title'], p.title)
        self.assertEqual(pdata['description'], p.description)
        self.assertEqual(pdata['adhocracy_type'], 'proposal')

    def test_export_badge(self):
        e = importexport.export_data(dict(
            include_user=True,
            user_personal=True,
            include_badge=True
        ))
        bdata = e['badge']
        assert len(bdata) >= 1
        mykey,myb = next((bkey,bd) for bkey,bd in bdata.items() if bd['title'] == self.badge.title)
        self.assertEqual(myb['color'], self.badge.color)
        self.assertTrue(myb['visible'])
        self.assertEqual(myb['description'], self.badge.description)
        self.assertEqual(myb['adhocracy_badge_type'], 'user')
        myu1 = next(u for u in e['user'].values() if u['email'] == self.u1.email)
        self.assertEqual(myu1['badges'], [mykey])

    def test_export_comments(self):
        p = testtools.tt_make_proposal(creator=self.u1, with_description=True)
        desc1 = testtools.tt_make_str()
        desc2 = testtools.tt_make_str()
        c1 = model.Comment.create(
            text=desc1,
            user=self.u1,
            topic=p.description,
            reply=None,
            variant='HEAD',
            sentiment=1)
        c2 = model.Comment.create(
            text=desc2,
            user=self.u2,
            topic=p.description,
            reply=c1,
            variant='HEAD',
            sentiment=-1)
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

        self.assertEqual(len(pdata['comments']), 1)
        cdata = next(iter(pdata['comments'].values()))
        self.assertEqual(cdata['text'], desc1)
        self.assertEqual(cdata['creator'], str(self.u1.id))
        self.assertEqual(cdata['sentiment'], 1)
        self.assertEqual(cdata['adhocracy_type'], 'comment')

        self.assertEqual(len(cdata['comments']), 1)
        cdata2 = next(iter(cdata['comments'].values()))
        self.assertEqual(cdata2['text'], desc2)
        self.assertEqual(cdata2['creator'], str(self.u2.id))
        self.assertEqual(cdata2['sentiment'], -1)
        self.assertEqual(cdata2['adhocracy_type'], 'comment')


    def test_rendering(self):
        e = importexport.export_data(dict(include_user=True, user_personal=True,
            user_password=True, include_badge=True))
        self.assertEqual(set(e.keys()), set(['metadata', 'user', 'badge']))

        formats = importexport.formats

        response = _MockResponse()
        zdata = formats.render(e, 'zip', 'test', response=response)
        with contextlib.closing(zipfile.ZipFile(io.BytesIO(zdata), 'r')) as zf:
            self.assertEqual(set(zf.namelist()), set(['metadata.json', 'user.json', 'badge.json']))
        zio = io.BytesIO(zdata)
        self.assertEqual(formats.detect_format(zio), 'zip')
        self.assertEqual(zio.read(), zdata)
        self.assertEqual(e, formats.read_data(io.BytesIO(zdata), 'zip'))
        self.assertEqual(e, formats.read_data(io.BytesIO(zdata), 'detect'))

        response = _MockResponse()
        jdata = formats.render(e, 'json', 'test', response=response)
        response = _MockResponse()
        jdata_dl = formats.render(e, 'json_download', 'test', response=response)
        self.assertEqual(jdata, jdata_dl)
        self.assertTrue(isinstance(jdata, bytes))
        jio = io.BytesIO(jdata)
        self.assertEqual(formats.detect_format(jio), 'json')
        self.assertEqual(jio.read(), jdata)
        self.assertEqual(e, formats.read_data(io.BytesIO(jdata), 'json'))
        self.assertEqual(e, formats.read_data(io.BytesIO(jdata), 'detect'))

        self.assertRaises(ValueError, formats.render, e, 'invalid', 'test', response=response)
        self.assertRaises(ValueError, formats.read_data, zdata, 'invalid')

        self.assertEqual(formats.detect_format(io.BytesIO()), 'unknown')

    def test_import_user(self):
        test_data = {
            "user": {
                "importexport_u1": {
                    "user_name": "importexport_u1",
                    "display_name": "Mr. Imported",
                    "email": "test@test_importexport.de",
                    "bio": "hey",
                    "locale": "de_DE",
                    "adhocracy_banned": True
                }
            }
        }
        opts = dict(include_user=True, user_personal=True, user_password=False)

        importexport.import_data(opts, test_data)
        u = model.User.find_by_email('test@test_importexport.de')
        self.assertTrue(u)
        self.assertEqual(u.user_name, 'importexport_u1')
        self.assertEqual(u.email, 'test@test_importexport.de')
        self.assertEqual(u.display_name, 'Mr. Imported')
        self.assertEqual(u.bio, 'hey')
        self.assertEqual(u.locale, 'de_DE')
        self.assertTrue(not u.banned)

        opts['replacement_strategy'] = 'skip'
        test_data['user']['importexport_u1']['display_name'] = 'Dr. Imported'
        importexport.import_data(opts, test_data)
        u = model.User.find_by_email('test@test_importexport.de')
        self.assertTrue(u)
        self.assertEqual(u.display_name, 'Mr. Imported')
        self.assertTrue(not u.banned)

        opts['replacement_strategy'] = 'update'
        opts['user_password'] = True
        importexport.import_data(opts, test_data)
        u = model.User.find_by_email('test@test_importexport.de')
        self.assertTrue(u)
        self.assertEqual(u.display_name, 'Dr. Imported')
        self.assertTrue(u.banned)

    def test_import_badge(self):
        test_data = {
            "badge": {
                "importexport_b1": {
                    "title": "importexport_b1",
                    "color": "mauve",
                    "adhocracy_badge_type": "user",
                    "visible": False,
                    "description": "test badge"
                }
            }
        }
        opts = dict(include_badge=True)

        importexport.import_data(opts, test_data)
        b = model.UserBadge.find('importexport_b1')
        self.assertTrue(b)
        self.assertEqual(b.title, 'importexport_b1')
        self.assertEqual(b.color, 'mauve')
        self.assertEqual(b.polymorphic_identity, 'user')
        self.assertTrue(not b.visible)
        self.assertEqual(b.description, 'test badge')


    def test_legacy(self):
        # Version 2 had 'users' instead of 'user'
        v2data = {'users': {}, 'metadata': {'version': 2}}
        self.assertTrue('users' in importexport.convert_legacy(v2data))

