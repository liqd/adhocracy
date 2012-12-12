
import contextlib
import io
import zipfile

import adhocracy.lib.importexport as importexport
from adhocracy.tests import TestController
import adhocracy.tests.testtools as testtools

class _MockResponse(object):
    pass


class ImportExportTest(TestController):
    def setUp(self):
        super(ImportExportTest, self).setUp()
        self.u1 = testtools.tt_make_user()
        self.u2 = testtools.tt_make_user()
        self.i1 = testtools.tt_make_instance('importexport_test', 'desc', self.u2)

    def test_transforms(self):
        tfs = importexport.transforms.gen_all({})
        self.assertTrue(any(tf.name.lower() == 'user' for tf in tfs))

        tfs = importexport.transforms.gen_active({})
        self.assertEquals(len(tfs), 0)


    def test_export_basic(self):
        e = importexport.export_data({})
        self.assertTrue(len(e) == 1)
        self.assertEquals(e['metadata']['type'], 'normsetting-export')
        self.assertTrue(e['metadata']['version'] >= 3)

    def test_export_user(self):
        e = importexport.export_data(dict(include_user=True, user_personal=True, user_password=True))
        users = e['user']
        self.assertTrue(len(users) >= 2)
        self.assertTrue(any(u['user_name'] == self.u1.user_name for u in users.values()))
        self.assertTrue(any(u['email'] == self.u2.email for u in users.values()))
        self.assertTrue(any(u['adhocracy_password'] == self.u1.password for u in users.values()))

    def test_export_anonymous(self):
        e = importexport.export_data(dict(include_user=True))
        users = e['user']
        self.assertTrue(len(users) >= 2)
        self.assertTrue(all(len(u) == 0 for u in users.values()))
        self.assertTrue(not any(self.u1.user_name in k for k in users.keys()))

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

# TODO test import as well

