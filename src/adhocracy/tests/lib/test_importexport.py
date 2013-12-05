# coding: utf-8

import contextlib
import datetime
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
        self.u1.gender = u'f'
        self.badge = model.UserBadge.create(
            title=u'importexport_badge"\'/\\ä↭𝕐',
            color=u'#ff00ff',
            visible=True,
            description=u'This badge tests',
        )
        self.u2 = testtools.tt_make_user()
        self.badge.assign(user=self.u1, creator=self.u2)
        self.instance = testtools.tt_make_instance(u'export_test',
                                                   label=u'export_test',
                                                   creator=self.u2)
        self.instance.label = u'test"\'/\\ä↭𝕐'
        self.instance.description = u'test"\'/\\ä↭𝕐'
        self.instance.required_majority = 0.42
        self.instance.activation_delay = 5
        self.instance.create_time = datetime.datetime.now()
        self.instance.access_time = datetime.datetime.now()
        self.instance.delete_time = None
        self.instance.default_group_id = 42
        self.instance.allow_adopt = False
        self.instance.allow_delegate = False
        self.instance.allow_propose = False
        self.instance.allow_index = False
        self.instance.hidden = False
        self.instance.locale = u'fr_FR'
        self.instance.css = u'test"\'/\\ä↭𝕐'
        self.instance.frozen = True
        self.instance.milestones = True
        self.instance.use_norms = False
        self.instance.require_selection = True
        self.instance.is_authenticated = True
        self.instance.hide_global_categories = True
        self.instance.editable_comments_default = False
        self.instance.editable_proposals_default = False
        self.instance.require_valid_email = False
        self.instance.allow_thumbnailbadges = True
        self.instance.thumbnailbadges_height = 42
        self.instance.thumbnailbadges_width = 42

    def test_transforms(self):
        tfs = importexport.transforms.gen_all({})
        self.assertTrue(any(tf.name.lower() == u'user' for tf in tfs))

        tfs = importexport.transforms.gen_active({})
        self.assertEqual(len(tfs), 0)

    def test_export_basic(self):
        e = importexport.export_data({})
        self.assertEqual(len(e), 1)
        self.assertEqual(e[u'metadata'][u'type'], u'normsetting-export')
        self.assertTrue(e[u'metadata'][u'version'] >= 3)

    def test_export_user(self):
        e = importexport.export_data(dict(include_user=True,
                                          user_personal=True,
                                          user_password=True))
        users = e[u'user'].values()
        self.assertTrue(len(users) >= 2)
        self.assertTrue(any(u[u'user_name'] == self.u1.user_name
                            for u in users))
        self.assertTrue(any(u[u'email'] == self.u2.email
                            for u in users))
        self.assertTrue(any(u[u'adhocracy_password'] == self.u1.password
                            for u in users))
        self.assertTrue(all(u'_' in u[u'locale'] for u in users))
        u1 = next(u for u in users if u[u'email'] == self.u1.email)
        self.assertEqual(u1[u'gender'], u'f')
        assert len(users) == len(model.User.all())

    def test_export_anonymous(self):
        e = importexport.export_data(dict(include_user=True))
        users = e[u'user']
        self.assertTrue(len(users) >= 2)
        self.assertTrue(all(len(u) == 0 for u in users.values()))
        self.assertTrue(not any(self.u1.user_name in k for k in users.keys()))
        u1 = next(iter(users))
        self.assertTrue(u'gender' not in u1)

    def test_export_instance(self):
        ed = importexport.export_data({
            u'include_instance': True,
            u'include_user': True,
            u'user_personal': True,
        })
        # Test that we don't spill non-representable objects by accident
        ex = importexport.render.render(ed, u'json', u'(title)',
                                        response=_MockResponse())
        e = importexport.parse.read_data(io.BytesIO(ex))

        self.assertTrue(u'instance' in e)
        self.assertTrue(len(e[u'instance']) >= 1)
        self.assertTrue(self.instance.key in e[u'instance'])
        idata = e[u'instance'][self.instance.key]
        self.assertEqual(idata[u'label'], self.instance.label)
        self.assertEqual(idata[u'key'], self.instance.key)

        user_id = idata[u'creator']
        assert user_id
        self.assertTrue(isinstance(user_id, (str, unicode)))
        self.assertEqual(e[u'user'][user_id][u'user_name'], self.u2.user_name)
        self.assertEqual(idata[u'adhocracy_type'], u'instance')

    def test_importexport_instance(self):
        opts = {
            u'include_instance': True
        }
        ed = importexport.export_data(opts)

        testdata = ed[u'instance'][self.instance.key]
        testdata[u'key'] += testtools.tt_make_str() + u'A'  # Test uppercase
        ed[u'instance'] = {testdata[u'key']: testdata}

        importexport.import_data(opts, ed)
        imported_instance = model.Instance.find(testdata[u'key'])
        self.assertTrue(imported_instance)

        INSTANCE_PROPS = [
            u'label', u'creator', u'description', u'required_majority',
            u'activation_delay',
            u'create_time', u'access_time', u'delete_time',
            u'default_group_id', u'allow_adopt', u'allow_delegate',
            u'allow_propose', u'allow_index', u'hidden', u'locale', u'css',
            u'frozen', u'milestones', u'use_norms', u'require_selection',
            u'is_authenticated', u'hide_global_categories',
            u'editable_comments_default', u'editable_proposals_default',
            u'require_valid_email', u'allow_thumbnailbadges',
            u'thumbnailbadges_height', u'thumbnailbadges_width',
        ]
        for p in INSTANCE_PROPS:
            imported = getattr(imported_instance, p)
            expected = getattr(self.instance, p)
            msg = (u'Instance.%s: Got %r, but expected %r' %
                   (p, imported, expected))
            self.assertEqual(expected, imported, msg)

    def test_export_proposal(self):
        p = testtools.tt_make_proposal(creator=self.u1)
        e = importexport.export_data({
            u"include_instance": True,
            u"include_instance_proposal": True,
            u"include_users": True,
        })
        idata = e[u'instance'][p.instance.key]
        self.assertTrue(u'proposals' in idata)
        pdata = idata[u'proposals'][str(p.id)]
        assert u'comments' not in pdata
        self.assertEqual(pdata[u'title'], p.title)
        self.assertEqual(pdata[u'description'], p.description)
        self.assertEqual(pdata[u'adhocracy_type'], u'proposal')

    def test_export_badge(self):
        e = importexport.export_data(dict(
            include_user=True,
            user_personal=True,
            include_badge=True
        ))
        bdata = e[u'badge']
        assert len(bdata) >= 1
        mykey, myb = next((bkey, bd) for bkey, bd in bdata.items()
                          if bd[u'title'] == self.badge.title)
        self.assertEqual(myb[u'color'], self.badge.color)
        self.assertTrue(myb[u'visible'])
        self.assertEqual(myb[u'description'], self.badge.description)
        self.assertEqual(myb[u'adhocracy_badge_type'], u'user')
        myu1 = next(u for u in e[u'user'].values()
                    if u[u'email'] == self.u1.email)
        self.assertEqual(myu1[u'badges'], [mykey])

    def test_export_comments(self):
        p = testtools.tt_make_proposal(creator=self.u1, with_description=True)
        desc1 = testtools.tt_make_str()
        desc2 = testtools.tt_make_str()
        c1 = model.Comment.create(
            text=desc1,
            user=self.u1,
            topic=p.description,
            reply=None,
            variant=u'HEAD',
            sentiment=1)
        c2 = model.Comment.create(
            text=desc2,
            user=self.u2,
            topic=p.description,
            reply=c1,
            variant=u'HEAD',
            sentiment=-1)
        assert p.description.comments

        e = importexport.export_data({
            "include_instance": True,
            "include_instance_proposal": True,
            "include_instance_proposal_comment": True,
            "include_users": True,
        })
        idata = e[u'instance'][p.instance.key]
        pdata = idata[u'proposals'][str(p.id)]
        assert u'comments' in pdata

        self.assertEqual(len(pdata[u'comments']), 1)
        cdata = next(iter(pdata[u'comments'].values()))
        self.assertEqual(cdata[u'text'], desc1)
        self.assertEqual(cdata[u'creator'], str(self.u1.id))
        self.assertEqual(cdata[u'sentiment'], 1)
        self.assertEqual(cdata[u'adhocracy_type'], u'comment')

        self.assertEqual(len(cdata[u'comments']), 1)
        cdata2 = next(iter(cdata[u'comments'].values()))
        self.assertEqual(cdata2[u'text'], desc2)
        self.assertEqual(cdata2[u'creator'], str(self.u2.id))
        self.assertEqual(cdata2[u'sentiment'], -1)
        self.assertEqual(cdata2[u'adhocracy_type'], u'comment')

    def test_rendering(self):
        e = importexport.export_data({
            u'include_user': True,
            u'user_personal': True,
            u'user_password': True,
            u'include_badge': True,
        })
        self.assertEqual(set(e.keys()), set([u'metadata', u'user', u'badge']))

        render = importexport.render.render
        parse = importexport.parse

        response = _MockResponse()
        zdata = render(e, u'zip', u'test', response=response)
        bio = io.BytesIO(zdata)
        with contextlib.closing(zipfile.ZipFile(bio, u'r')) as zf:
            expected_files = set([u'metadata.json', u'user.json',
                                  u'badge.json'])
            self.assertEqual(set(zf.namelist()), expected_files)
        zio = io.BytesIO(zdata)
        self.assertEqual(parse.detect_format(zio), u'zip')
        self.assertEqual(zio.read(), zdata)
        self.assertEqual(e, parse.read_data(io.BytesIO(zdata), u'zip'))
        self.assertEqual(e, parse.read_data(io.BytesIO(zdata), u'detect'))

        response = _MockResponse()
        jdata = render(e, u'json', u'test', response=response)
        response = _MockResponse()
        jdata_dl = render(e, u'json_download', u'test', response=response)
        self.assertEqual(jdata, jdata_dl)
        self.assertTrue(isinstance(jdata, bytes))
        jio = io.BytesIO(jdata)
        self.assertEqual(parse.detect_format(jio), u'json')
        self.assertEqual(jio.read(), jdata)
        self.assertEqual(e, parse.read_data(io.BytesIO(jdata), u'json'))
        self.assertEqual(e, parse.read_data(io.BytesIO(jdata), u'detect'))

        self.assertRaises(ValueError, render, e, u'invalid', u'test',
                          response=response)
        self.assertRaises(ValueError, parse.read_data, zdata, u'invalid')

        self.assertEqual(parse.detect_format(io.BytesIO()), u'unknown')

    def test_import_user(self):
        test_data = {
            u"user": {
                u"importexport_u1": {
                    u"user_name": u"importexport_u1",
                    u"display_name": u"Mr. Imported",
                    u"email": u"test@test_importexport.de",
                    u"bio": u"hey",
                    u"locale": u"de_DE",
                    u"adhocracy_banned": True
                }
            }
        }
        opts = dict(include_user=True, user_personal=True, user_password=False)

        importexport.import_data(opts, test_data)
        u = model.User.find_by_email(u'test@test_importexport.de')
        self.assertTrue(u)
        self.assertEqual(u.user_name, u'importexport_u1')
        self.assertEqual(u.email, u'test@test_importexport.de')
        self.assertEqual(u.display_name, u'Mr. Imported')
        self.assertEqual(u.bio, u'hey')
        self.assertEqual(str(u.locale), u'de_DE')
        self.assertTrue(not u.banned)

        opts[u'replacement_strategy'] = u'skip'
        testdata_user = test_data[u'user'][u'importexport_u1']
        testdata_user[u'display_name'] = u'Dr. Imported'
        importexport.import_data(opts, test_data)
        u = model.User.find_by_email(u'test@test_importexport.de')
        self.assertTrue(u)
        self.assertEqual(u.display_name, u'Mr. Imported')
        self.assertTrue(not u.banned)

        opts[u'replacement_strategy'] = u'update'
        opts[u'user_password'] = True
        importexport.import_data(opts, test_data)
        u = model.User.find_by_email(u'test@test_importexport.de')
        self.assertTrue(u)
        self.assertEqual(u.display_name, u'Dr. Imported')
        self.assertTrue(u.banned)

    def test_import_badge(self):
        test_data = {
            u"badge": {
                u"importexport_b1": {
                    u"title": u"importexport_b1",
                    u"color": u"mauve",
                    u"adhocracy_badge_type": u"user",
                    u"visible": False,
                    u"description": u"test badge"
                }
            }
        }
        opts = {
            u'include_badge': True
        }

        importexport.import_data(opts, test_data)
        b = model.UserBadge.find(u'importexport_b1')
        self.assertTrue(b)
        self.assertEqual(b.title, u'importexport_b1')
        self.assertEqual(b.color, u'mauve')
        self.assertEqual(b.polymorphic_identity, u'user')
        self.assertTrue(not b.visible)
        self.assertEqual(b.description, u'test badge')

    def test_legacy(self):
        # Version 2 had 'users' instead of 'user'
        v2data = {'users': {}, 'metadata': {'version': 2}}
        self.assertTrue(u'users' in importexport.convert_legacy(v2data))

    def test_time_encoding(self):
        from adhocracy.lib.importexport import transforms
        t1 = transforms.decode_time(u'2013-04-19T11:27:13Z')
        self.assertEqual(t1.microsecond, 0)
        t1_reencoded = transforms.decode_time(transforms.encode_time(t1))
        self.assertEqual(t1, t1_reencoded)

        t2 = transforms.decode_time(u'2013-04-19T11:27:23.123456')
        self.assertEqual(t2.microsecond, 123456)
        t2_reencoded = transforms.decode_time(transforms.encode_time(t2))
        self.assertEqual(t2, t2_reencoded)
