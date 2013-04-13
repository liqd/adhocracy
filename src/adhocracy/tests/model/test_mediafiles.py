# coding=utf-8
from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user


class TestMediaFileController(TestController):

    def test_create_and_get_mediafiles(self):
        #setup
        from adhocracy.model.mediafile import MediaFile
        from adhocracy.model.instance import Instance
        instance = Instance.find(u'test')
        # Create MediaFile with instance reference
        MediaFile.create(u"name", instance=instance)
        # Create MediaFile without instance reference
        MediaFile.create(u"name", instance=None)
        # We can get all MediaFiles by using `MediaFile`
        self.assertEqual(len(MediaFile.all()), 1)
        self.assertEqual(len(MediaFile.all(instance=instance)), 1)
        self.assertEqual(len(MediaFile.all_q().all()), 2)


class TestDelegateableController(TestController):

    def _make_content(self):
        """Returns creator, delegateable and mediafile"""
        from adhocracy.model.proposal import Proposal
        from adhocracy.model.instance import Instance
        from adhocracy.model.mediafile import MediaFile
        instance = Instance.find('test')
        creator = tt_make_user('creator')
        delegateable = Proposal.create(instance, u"labeld", creator)
        mediafile = MediaFile.create(u'name',)

        return creator, delegateable, mediafile

    def test_delegateablemediafiles_created(self):
        #setup
        from adhocracy.model.mediafile import DelegateableMediaFiles
        from adhocracy.model import meta
        creator, delegateable, mediafile = self._make_content()
        # create the delegateable mediafile
        mediafile.assign(delegateable, creator)
        delegateablemediafiles = \
            meta.Session.query(DelegateableMediaFiles).first()
        self.assertTrue(delegateablemediafiles.creator is creator)
        self.assertTrue(delegateablemediafiles.delegateable is delegateable)
        self.assertTrue(delegateablemediafiles.mediafile is mediafile)
        # test the references on the mediafiled delegateable
        self.assertEqual(delegateable.mediafiles, [mediafile])
        # test the references on the mediafile
        self.assertTrue(delegateable.mediafiles[0].delegateables
                        == mediafile.delegateables
                        == [delegateable])

    def test_remove_mediafile_from_delegateable(self):
        #setup
        from adhocracy.model.mediafile import DelegateableMediaFiles
        from adhocracy.model import meta
        creator, delegateable, mediafile = self._make_content()
        mediafile.assign(delegateable, creator)
        #remove mediafile from delegateable
        delegateable.mediafiles.remove(mediafile)
        self.assertEqual(delegateable.mediafiles, [])
        self.assertEqual(mediafile.delegateables, [])
        self.assertEqual(meta.Session.query(DelegateableMediaFiles).count(), 0)

    def test_remove_delegateable_from_mediafile(self):
        #setup
        from adhocracy.model.mediafile import DelegateableMediaFiles
        from adhocracy.model import meta
        creator, delegateable, mediafile = self._make_content()
        mediafile.assign(delegateable, creator)
        #remove delegateable from mediafile
        mediafile.delegateables.remove(delegateable)
        self.assertEqual(mediafile.delegateables, [])
        self.assertEqual(delegateable.mediafiles, [])
        self.assertEqual(meta.Session.query(DelegateableMediaFiles).count(), 0)
