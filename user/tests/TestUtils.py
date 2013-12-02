# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.sites.models import Site
from django.test import TestCase
from facebook import FacebookAPI
from PIL import Image

from commons.tests.utils import TEST_PICTURE
from user.models import BaseUser
from user.tests.factories import BaseUserFactory
from user.utils import unique_slugify, resize, absolute_url, get_facebook, clean_fb_session


class UtilsTest(TestCase):
    def test_unique_slugify(self):
        """Test unique_slugify utility function."""
        # Create user
        user = BaseUserFactory()

        # unique_slugify append unique token to existing slugs
        unique_slug = unique_slugify(user.slug, BaseUser)
        self.assertNotEqual(user.slug, unique_slug)

        # unique_slugify return intact slug if if doesn't exist
        unique_slug = unique_slugify(u'azertyuiop', BaseUser)
        self.assertEqual(u'azertyuiop', unique_slug)

    def test_resize(self):
        """Test resize utility function on 40*30 png."""
        img = Image.open(TEST_PICTURE)
        w, h = img.size
        image_ratio = float(h) / float(w)

        # Resize with same ratio
        width, height = (20, 15)
        assert float(height) / float(width) == image_ratio
        new_img = Image.open(resize(img, (width, height), 'png'))
        self.assertEqual(new_img.size, (width, height))

        # Resize with portrait ratio
        width, height = (10, 30)
        assert float(height) / float(width) > image_ratio
        new_img = Image.open(resize(img, (width, height), 'png'))
        self.assertEqual(new_img.size, (width, height))

        # Resize with landscape ratio
        width, height = (40, 15)
        assert float(height) / float(width) < image_ratio
        new_img = Image.open(resize(img, (width, height), 'png'))
        self.assertEqual(new_img.size, (width, height))

    def test_absolute_url(self):
        domain = 'http://' + Site.objects.get(pk=settings.SITE_ID).domain
        relative_url = '/home'
        abs_url = absolute_url(relative_url)

        self.assertNotEqual(abs_url, relative_url)
        self.assertTrue(abs_url.startswith(domain))
        self.assertTrue(abs_url.endswith(relative_url))

    def test_get_facebook(self):
        self.assertIsInstance(get_facebook(), FacebookAPI)

    def test_clean_fb_session(self):
        # create fake session
        session = dict()

        # Test session cleaning without data
        clean_fb_session(session)
        self.assertIsNone(session.get('fb_token'))
        self.assertIsNone(session.get('fb_id'))

        # Populate session with fake fb data
        session['fb_token'] = {"access_token": "rty"}
        session['fb_id'] = 12345
        assert session.get('fb_token')
        assert session.get('fb_id')

        # Test session cleaning
        clean_fb_session(session)
        self.assertIsNone(session.get('fb_token'))
        self.assertIsNone(session.get('fb_id'))
