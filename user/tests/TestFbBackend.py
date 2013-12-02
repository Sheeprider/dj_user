from django.contrib.auth import authenticate
from django.test import TestCase
from facebook import GraphAPIError, FacebookAuthError
from mock import patch

from user.backends import FacebookBackend
from user.tests.factories import BaseUserFactory

VALID_TOKEN = 'valid_token'
INVALID_TOKEN = 'invalid_token'
VALID_ID = 1234567890
INVALID_ID = 123
VALID_EMAIL = 'email@domain.com'
VALID_CODE = 'azerty'
INVALID_CODE = 'qwerty'
AVATAR_URL = 'http://avatar/url'

def get(self, path, *args, **kwargs):
    """Mock GraphAPI.get ."""
    if not self.access_token == VALID_TOKEN:
        raise GraphAPIError('Invalid token: %s.' % self.access_token)
    else:
        if path == 'me':
            return {'id': VALID_ID, 'email': VALID_EMAIL}
        elif path == 'me/picture':
            return {'data': {'url': AVATAR_URL}}
        else:
            raise GraphAPIError('Invalid path: %s.' % path)


def get_access_token(self, code, *args, **kwargs):
    """Mock FacebookAPI.get_access_token ."""
    if code == VALID_CODE:
        return {'access_token': VALID_TOKEN}
    raise FacebookAuthError('Invalid code: %s.' % code)


@patch('user.backends.GraphAPI.get', new=get)
class FbBackendTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = BaseUserFactory(
            _fb_token=VALID_TOKEN,
            _fb_id=VALID_ID,)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def test_authenticate(self):
        # Auth without token
        self.assertIsNone(authenticate())
        # Auth with missing fb_id
        self.assertIsNone(authenticate(access_token=VALID_TOKEN))
        # Auth with invalid token and fb_id
        self.assertIsNone(authenticate(access_token=INVALID_TOKEN, fb_id=INVALID_ID))
        # Auth with invalid fb_id
        self.assertIsNone(authenticate(access_token=VALID_TOKEN, fb_id=INVALID_ID))
        # Auth with invalid token
        self.assertIsNone(authenticate(access_token=INVALID_TOKEN, fb_id=VALID_ID))
        # Auth with valid credentials
        user = authenticate(access_token=VALID_TOKEN, fb_id=VALID_ID)
        self.assertIsNotNone(user)
        self.assertTrue(user.is_authenticated())
        self.assertEquals(user.backend, 'user.backends.FacebookBackend')

    def test_get_user(self):
        backend = FacebookBackend()

        self.assertIsNone(backend.get_user(0))
        user = backend.get_user(self.user.id)
        self.assertIsNotNone(user)
        self.assertEquals(user, self.user)
