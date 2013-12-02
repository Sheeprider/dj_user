# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from mock import patch

from user.models import _lazy_user_model
from user.tests.factories import BaseUserFactory
from user.tests.TestFbBackend import get, get_access_token, VALID_TOKEN, VALID_ID, AVATAR_URL


class UserModelTest(TestCase):
    def setUp(self):
        """Create user."""
        self.user = BaseUserFactory()

    def tearDown(self):
        """Delete user."""
        self.user.delete()

    def test_user_methods(self):
        """Test user basic methods."""
        # Both methods should return user's name
        self.assertEqual(self.user.get_full_name(), self.user.name)
        self.assertEqual(self.user.get_short_name(), self.user.name)

        # These attributes are null by default
        self.assertIsNone(self.user.avatar)
        self.assertIsNone(self.user.small_avatar)

    def test_fb_properties(self):
        # Test fb_token saves and return a dict
        fb_token = {"aze": "rty"}
        self.user.fb_token = fb_token
        self.assertEqual(self.user.fb_token, fb_token)

        # Test fb_token can save a null value
        self.user.fb_token = None
        self.assertEqual(self.user.fb_token, None)

        # Test fb_id can save a null value
        self.user.fb_id = 12345
        assert self.user.fb_id == 12345
        self.user.fb_id = None
        self.assertEqual(self.user.fb_id, None)

        # Create user with fb_id
        BaseUserFactory(fb_id=1337)
        # Try to assign same fb_id on different user
        with self.assertRaises(ValidationError):
            self.user.fb_id = 1337

    def test__lazy_user_model(self):
        email, pwd, slug, name = "maxime@smoothie-creative.com", "password", "maxime", "Maxime"
        self.assertEqual(
            _lazy_user_model(email=email, password=pwd, slug=slug, name=name),
            get_user_model()(email=email, password=pwd, slug=slug, name=name)
        )

    def test___repr__(self):
        self.assertEqual(self.user.__repr__(), "<{0}: {1}>".format(self.user.__class__.__name__, self.user.email))

    def test___str__(self):
        self.assertEqual(self.user.__str__(), self.user.email)
        self.assertIsInstance(self.user.__str__(), str)

    def test_fb_is_connected_with_not_connected_user(self):
        self.assertFalse(self.user.fb_is_connected())

    def test_fb_is_connected_with_connected_user(self):
        self.user.fb_token = {"access_token": VALID_TOKEN}
        self.user.fb_id = VALID_ID
        self.user.save()

        self.assertTrue(self.user.fb_is_connected())

    def test_fb_avatar_with_not_connected_user(self):
        self.assertIsNone(self.user.fb_avatar())

    def test_fb_avatar_with_connected_user(self):
        self.user.fb_token = {"access_token": VALID_TOKEN}
        self.user.fb_id = VALID_ID
        self.user.save()

        with patch('user.backends.GraphAPI.get', new=get):
            with patch('user.utils.FacebookAPI.get_access_token', new=get_access_token):
                avatar = self.user.fb_avatar()

        self.assertIsNotNone(avatar)
        self.assertEquals(avatar, AVATAR_URL)
