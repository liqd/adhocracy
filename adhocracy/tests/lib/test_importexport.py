

import adhocracy.lib.importexport as importexport
from adhocracy.tests import TestController
import adhocracy.tests.testtools as testtools


class ImportExportTest(TestController):
    def setUp(self):
        super(ImportExportTest, self).setUp()
        self.u1 = testtools.tt_make_user()
        self.u2 = testtools.tt_make_user()
        self.i1 = testtools.tt_make_instance('importexport_test', 'desc', self.u2)

    def test_transforms(self):
        tfs = importexport.transforms.gen_all({})
        assert any(tf.name.lower() == 'user' for tf in tfs)

        tfs = importexport.transforms.gen_active({})
        assert len(tfs) == 0


    def test_export_basic(self):
        e = importexport.export_data({})
        assert len(e) == 1
        self.assertEquals(e['metadata']['type'], 'normsetting-export')
        self.assertTrue(e['metadata']['version'] >= 3)

    def test_export_user(self):
        e = importexport.export_data(dict(include_user=True, user_personal=True, user_password=True))
        users = e['user']
        assert len(users) >= 2
        assert any(u['user_name'] == self.u1.user_name for u in users.values())
        assert any(u['email'] == self.u2.email for u in users.values())
        assert any(u['adhocracy_password'] == self.u1.password for u in users.values())

    def test_export_anonymous(self):
        e = importexport.export_data(dict(include_user=True))
        users = e['user']
        assert len(users) >= 2
        assert all(len(u) == 0 for u in users.values())
        assert not any(self.u1.user_name in k for k in users.keys()) 

# TODO test import as well
# TODO test export to Zip

