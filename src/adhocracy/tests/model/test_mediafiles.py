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

    def test_repr_mediafile(self):
        from adhocracy.model.mediafile import MediaFile
        mediafile = MediaFile.create(u"name", instance=None)
        self.assertEqual(mediafile.__repr__(), "<MediaFile(1,name)>")


class TestDelegateableController(TestController):

    def _make_content(self):
        """Returns creator, delegateable and mediafile"""
        from adhocracy.model.proposal import Proposal
        from adhocracy.model.instance import Instance
        from adhocracy.model.mediafile import MediaFile
        instance = Instance.find('test')
        creator = tt_make_user('creator')
        delegateable = Proposal.create(instance, u"labeld", creator)
        mediafile = MediaFile.create(u'name')

        return creator, delegateable, mediafile

    def test_delegateablemediafiles_created(self):
        #setup
        from adhocracy.model.mediafile import DelegateableMediaFiles
        from adhocracy.model import meta
        creator, delegateable, mediafile = self._make_content()
        # create the delegateable mediafile
        mediafile.assignDelegateable(delegateable, creator)
        delegateablemediafile = \
            meta.Session.query(DelegateableMediaFiles).first()
        self.assertTrue(delegateablemediafile.creator is creator)
        self.assertTrue(delegateablemediafile.delegateable is delegateable)
        self.assertTrue(delegateablemediafile.mediafile is mediafile)
        self.assertEqual(delegateablemediafile.__repr__(),
                         '<delegateablemediafiles(1, mediafile 1/name for '
                         'delegateable 2)>')
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
        mediafile.assignDelegateable(delegateable, creator)
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
        mediafile.assignDelegateable(delegateable, creator)
        #remove delegateable from mediafile
        mediafile.delegateables.remove(delegateable)
        self.assertEqual(mediafile.delegateables, [])
        self.assertEqual(delegateable.mediafiles, [])
        self.assertEqual(meta.Session.query(DelegateableMediaFiles).count(), 0)


class TestCommentController(TestController):

    def _make_content(self):
        """Returns creator, comment and mediafile"""
        from adhocracy.model.comment import Comment
        from adhocracy.model.proposal import Proposal
        from adhocracy.model.instance import Instance
        from adhocracy.model.mediafile import MediaFile
        instance = Instance.find('test')
        creator = tt_make_user('creator')
        topic = Proposal.create(instance, u"labeld", creator)
        comment = Comment.create(u"text", creator, topic)
        mediafile = MediaFile.create(u'name')

        return creator, comment, mediafile

    def test_commentmediafiles_created(self):
        #setup
        from adhocracy.model.mediafile import CommentMediaFiles
        from adhocracy.model import meta
        creator, comment, mediafile = self._make_content()
        # create the comment mediafile
        mediafile.assignComment(comment, creator)
        commentmediafile = \
            meta.Session.query(CommentMediaFiles).first()
        self.assertTrue(commentmediafile.creator is creator)
        self.assertTrue(commentmediafile.comment is comment)
        self.assertTrue(commentmediafile.mediafile is mediafile)
        # test the references on the mediafiled comment
        self.assertEqual(comment.mediafiles, [mediafile])
        # test the references on the mediafile
        self.assertTrue(comment.mediafiles[0].comments
                        == mediafile.comments
                        == [comment])

    def test_remove_mediafile_from_comment(self):
        #setup
        from adhocracy.model.mediafile import CommentMediaFiles
        from adhocracy.model import meta
        creator, comment, mediafile = self._make_content()
        mediafile.assignComment(comment, creator)
        #remove mediafile from comment
        comment.mediafiles.remove(mediafile)
        self.assertEqual(comment.mediafiles, [])
        self.assertEqual(mediafile.comments, [])
        self.assertEqual(meta.Session.query(CommentMediaFiles).count(), 0)

    def test_remove_comment_from_mediafile(self):
        #setup
        from adhocracy.model.mediafile import CommentMediaFiles
        from adhocracy.model import meta
        creator, comment, mediafile = self._make_content()
        mediafile.assignComment(comment, creator)
        #remove comment from mediafile
        mediafile.comments.remove(comment)
        self.assertEqual(mediafile.comments, [])
        self.assertEqual(comment.mediafiles, [])
        self.assertEqual(meta.Session.query(CommentMediaFiles).count(), 0)
