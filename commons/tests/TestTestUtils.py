# -*- coding: utf-8 -*-
from unittest import TestCase

from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.cache import SessionStore

from commons.tests.utils import _request, get_request, post_request, delete_request


class TestUtilsTest(TestCase):
    """
    Yo Dawg, I heard you like tests, so I put a test in your tests so you can test your tests.

    Tests utilities functions used for tests on the whole project.

    ”"""
    def test__request(self):
        # Create a request with default parameters
        r = _request({})
        self.assertIsInstance(r, HttpRequest)

        self.assertIsInstance(r.user, AnonymousUser)
        self.assertIsInstance(r.session, SessionStore)
        self.assertTrue(r._dont_enforce_csrf_checks)

    def test__request__path(self):
        path = '/not/the/default/path'
        r = _request({}, path=path)
        self.assertEqual(r.path, path)

    def test__request__default_method(self):
        r = _request({})
        self.assertEqual(r.method, 'GET')

    def test__request__ajax(self):
        # Test default parameter
        r = _request({})
        self.assertFalse(r.is_ajax())
        r = _request({}, ajax=True)
        self.assertTrue(r.is_ajax())

    def test_get_request(self):
        r = get_request()
        self.assertEqual(r.method, 'GET')

    def test_post_request(self):
        r = post_request()
        self.assertEqual(r.method, 'POST')

    def test_delete_request(self):
        r = delete_request()
        self.assertEqual(r.method, 'DELETE')
