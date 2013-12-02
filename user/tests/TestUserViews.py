# -*- coding: utf-8 -*-
import simplejson as json
from urlparse import urlparse

from django.conf import settings
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase
from mock import patch

from commons.tests.utils import get_request, post_request
from user import views
from user.forms import CustomAuthenticationForm
from user.models import BaseUser
from user.tests.factories import BaseUserFactory
from user.tests.TestFbBackend import get, get_access_token, VALID_TOKEN, INVALID_TOKEN, VALID_ID, VALID_EMAIL, VALID_CODE, INVALID_CODE


class AnonymousViewsTest(TestCase):
    def test_home(self):
        """Test home view."""
        r = get_request()
        response = views.home(r)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, 'pages/home.html')

    def test_studentcreationview_post_with_valid_data(self):
        old_user_count = BaseUser.objects.count()
        valid_data = {'email': 'maxime@smoothie-creative.com', 'password1': 'password', 'password2': 'password', 'cgu': True}
        r = post_request(valid_data)
        view = views.StudentCreationView.as_view()
        response = view(r)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], reverse(settings.LOGIN_URL))
        self.assertEqual(BaseUser.objects.count(), old_user_count + 1)
        self.assertTrue(BaseUser.objects.filter(email=valid_data['email']).exists())

    def test__baseuser_delete_get_without_user(self):
        r = get_request()
        with self.assertRaises(Http404):
            views._baseuser_delete(r)

    def test__baseuser_edit_get_without_user(self):
        r = get_request()
        with self.assertRaises(Http404):
            views._baseuser_edit(r)

    def test_login_is_django_login_view(self):
        r = get_request()
        response = views.login(r, template_name='user/login.html')
        dj_response = login(r, template_name='user/login.html', authentication_form=CustomAuthenticationForm)
        response.render()
        dj_response.render()
        self.assertEqual(response.status_code, dj_response.status_code)
        self.assertEqual(response.content, dj_response.content)


class UserViewsTest(TestCase):
    def setUp(self):
        self.user = BaseUserFactory()

    def test_login_redirects_authenticated_user(self):
        r = get_request()
        r.user = self.user
        response = views.login(r, template_name='user/login.html')
        self.assertEqual(response['location'], reverse(settings.LOGIN_REDIRECT_URL))

    def test_login_redirects_authenticated_user_to_next_url(self):
        r = get_request({'next': '/redirect_url'})
        r.user = self.user
        response = views.login(r, template_name='user/login.html')
        self.assertEqual(response['location'], '/redirect_url')

    def test__baseuser_delete_get_with_student(self):
        r = get_request()
        r.user = self.user
        response = views._baseuser_delete(r)
        self.assertEqual(response.status_code, 200)

    def test__baseuser_delete_post_valid_data_delete_student(self):
        old_user_count = BaseUser.objects.count()
        valid_data = {'password': 'password'}
        r = post_request(valid_data)
        r.user = self.user
        response = views._baseuser_delete(r)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], reverse('user:logout'))
        self.assertEqual(BaseUser.objects.count(), old_user_count - 1)

    def test__baseuser_delete_post_valid_data_ajax_return_json(self):
        old_user_count = BaseUser.objects.count()
        valid_data = {'password': 'password'}
        r = post_request(valid_data, ajax=True)
        r.user = self.user
        response = views._baseuser_delete(r)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], "application/json")
        self.assertEqual(BaseUser.objects.count(), old_user_count - 1)
        json.loads(response.content)

    def test__baseuser_delete_post_invalid_data_ajax_return_json(self):
        invalid_data = {'password': 'bad_password'}
        r = post_request(invalid_data, ajax=True)
        r.user = self.user
        response = views._baseuser_delete(r)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], "application/json")
        json.loads(response.content)

    def test__baseuser_edit_get_with_student(self):
        r = get_request()
        r.user = self.user
        response = views._baseuser_delete(r)
        self.assertEqual(response.status_code, 200)

    def test__baseuser_edit_post_valid_data_update_user_in_session(self):
        data = {'name': 'toto', 'email': self.user.email}
        r = post_request(data)
        r.user = self.user
        response = views._baseuser_edit(r)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(r.user.name, 'toto')


@patch('user.backends.GraphAPI.get', new=get)
@patch('user.utils.FacebookAPI.get_access_token', new=get_access_token)
class FacebookAPIViewsTest(TestCase):
    """Test views using the Facebook API."""
    def setUp(self):
        self.user = BaseUserFactory()

    def test_fb_auth(self):
        """Test fb_auth view."""
        r = get_request()
        response = views.fb_auth(r)
        self.assertEqual(response.status_code, 302)
        location = urlparse(response['location'])
        self.assertEqual(location.scheme, 'https')
        self.assertEqual(location.netloc, 'www.facebook.com')
        self.assertEqual(location.path, '/dialog/oauth')

    def test_fb_callback_without_code(self):
        r = get_request()
        response = views.fb_callback(r)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], reverse('user:student.register'))

    def test_fb_callback_without_code_and_authenticated_student(self):
        r = get_request()
        r.user = self.user
        response = views.fb_callback(r)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], reverse('user:edit'))

    def test_fb_callback_with_code_and_authenticated_student_associate_account(self):
        r = get_request({'code': VALID_CODE})
        r.user = self.user
        response = views.fb_callback(r)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], reverse('user:edit'))

        self.assertEqual(r.user.fb_id, VALID_ID)
        self.assertIsNotNone(r.user.fb_token)

    def test_studentcreationview_get_with_invalid_token(self):
        r = get_request()
        r.session['fb_token'] = {'access_token': INVALID_TOKEN}
        view = views.StudentCreationView.as_view()
        response = view(r)
        self.assertEqual(response.status_code, 200)
        # Invalid fb_token should get cleaned from session
        self.assertNotIn('fb_token', r.session)

    def test_studentcreationview_get_with_valid_token(self):
        r = get_request()
        r.session['fb_token'] = {'access_token': VALID_TOKEN}
        view = views.StudentCreationView.as_view()
        with patch('user.views.StudentCreationView.initial') as mock_initial:
            response = view(r)

        self.assertEqual(response.status_code, 200)
        # Valid fb_token should not get cleaned from session
        self.assertIn('fb_token', r.session)
        # Valid fb_token should get view.initial updated
        mock_initial.update.assert_called_once()
        expecte_args = [({'fb_id': VALID_ID, 'fb_token':{'access_token': VALID_TOKEN}, 'email': VALID_EMAIL}, ), ]
        self.assertEqual(mock_initial.update.call_args_list, expecte_args)

    def test_fb_callback_with_invalid_code(self):
        r = get_request({'code': INVALID_CODE})
        response = views.fb_callback(r)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], reverse('user:login'))

    def test_fb_callback__with_valid_code_redirect_to_account_creation(self):
        r = get_request({'code': VALID_CODE})
        response = views.fb_callback(r)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], reverse('user:student.register'))

    def test_fb_callback__with_valid_code_from_valid_account_logs_user(self):
        self.user.fb_token = {"access_token": VALID_TOKEN}
        self.user.fb_id = VALID_ID
        self.user.save()

        r = get_request({'code': VALID_CODE})
        response = views.fb_callback(r)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], reverse('user:edit'))
        self.assertTrue(r.user.is_authenticated())
        self.assertEqual(r.user, self.user)

    def test__fb_disconnect(self):
        r = get_request()
        r.user = self.user
        response = views._fb_disconnect(r)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], reverse('user:edit'))

        self.assertIsNone(r.user.fb_token)
        self.assertIsNone(r.user.fb_id)
