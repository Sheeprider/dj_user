# -*- coding: utf-8 -*-
import os

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.cache import SessionStore
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

TEST_PICTURE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'img', 'picture.png')


def _request(data, path='/fake_path', method='get', ajax=False):
    """
    Return a request with emulated session and user.
    It doesn't enforce csrf checks.
    Use for tests only !
    """
    if ajax:
        r = getattr(RequestFactory(), method)(path, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    else:
        r = getattr(RequestFactory(), method)(path, data)
    setattr(r, 'user', AnonymousUser())
    setattr(r, 'session', SessionStore())
    setattr(r, '_dont_enforce_csrf_checks', True)
    return r


def get_request(data={}, *args, **kwargs):
    """Return a get request."""
    return _request(data, *args, **kwargs)


def post_request(data={}, *args, **kwargs):
    """Return a post request."""
    return _request(data, method='post', *args, **kwargs)


def delete_request(data={}, *args, **kwargs):
    """Return a delete request."""
    return _request(data, method='delete', *args, **kwargs)


def get_test_picture():
    with open(TEST_PICTURE, 'rb') as fp:
        return SimpleUploadedFile('picture.png', fp.read(), 'image/png')
