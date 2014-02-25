#!/usr/bin/env python
# coding: utf-8

from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user
from adhocracy.model import meta, Velruse as VelruseModel
from adhocracy.controllers.velruse import VelruseController


class TestVelruseController(TestController,
                            VelruseController):

    def test_new_facebook_user(self):

        user, velruse_user = VelruseController._create(self,
                                                       "test_user",
                                                       "Jonny@test.de",
                                                       "facebook",
                                                       "73478347348")

        self.assertEqual(user.id, velruse_user.user_id)

    def test_existing_user_is_matched_by_email(self):

        # his email is Jonny@test.de
        user = tt_make_user("Jonny")

        user2, velruse_user = VelruseController._create(self,
                                                        "test_user",
                                                        "Jonny@test.de",
                                                        "facebook",
                                                        "392833324324")

        self.assertEqual(user, user2)

    def test_connect_existing_user_same_email(self):

        user = tt_make_user("Jonny")

        # his email is Jonny@test.de
        velruse_user = VelruseModel.connect(user,
                                            "facebook",
                                            "239857329847",
                                            "Jonny@test.de",
                                            True)

        meta.Session.commit()

        self.assertNotEqual(velruse_user, None)
        self.assertEqual(user.id, velruse_user.user_id)
        self.assertEqual(user.activation_code, None)

    def test_connect_existing_user_different_email(self):

        user = tt_make_user("Jonny")

        # his email is Jonny@test.de
        velruse_user = VelruseModel.connect(user,
                                            "facebook",
                                            "328957239052",
                                            "DifferentEmail@test.de",
                                            True)

        meta.Session.commit()

        self.assertNotEqual(velruse_user, None)
        self.assertEqual(user.id, velruse_user.user_id)
        self.assertNotEqual(user.activation_code, None)
