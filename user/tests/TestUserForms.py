from django.template.defaultfilters import filesizeformat
from django.test import TestCase
from django.test.utils import override_settings

from commons.tests.utils import get_test_picture
from user.forms import BaseUserCreationForm, BaseUserEditionForm, BaseUserDeleteForm
from user.models import BaseUser
from user.tests.factories import BaseUserFactory
from user.utils import unique_slugify
# LiveUserMixin as_divs, _html_output => webtest


class BaseUserCreationFormTest(TestCase):
    def BaseUserstudentcreationform_clean_email(self):
        field = 'email'
        user = BaseUserFactory()

        duplicate_email_form = BaseUserCreationForm({'email': user.email})
        duplicate_email_form.is_valid()
        self.assertIn(field, duplicate_email_form.errors)
        self.assertIn(BaseUserCreationForm.error_messages['duplicate_email'], duplicate_email_form.errors.get(field))

        valid_email_form = BaseUserCreationForm({'email': 'maxime@smoothie-creative.com'})
        valid_email_form.is_valid()
        self.assertNotIn(field, valid_email_form.errors)

    def BaseUserstudentcreationform_clean_password2(self):
        field = 'password%s'

        password_mismatch_form = BaseUserCreationForm({field % 1: 'password', field % 2: 'not_password'})
        password_mismatch_form.is_valid()
        self.assertIn(field % 2, password_mismatch_form.errors)
        self.assertIn(BaseUserCreationForm.error_messages['password_mismatch'], password_mismatch_form.errors.get(field % 2))

        valid_password_form = BaseUserCreationForm({field % 1: 'password', field % 2: 'password'})
        valid_password_form.is_valid()
        self.assertNotIn(field % 2, valid_password_form.errors)

    def BaseUserstudentcreationform_save(self):
        """Check that new user's slug and name are first part of email, uniquely slugified."""
        unique_slug = unique_slugify('baptiste', BaseUser)
        valid_form = BaseUserCreationForm({
            'email': 'baptiste@smoothie-creative.com',
            'cgu': True,
            'password1': 'password',
            'password2': 'password',
        })
        assert valid_form.is_valid()
        valid_form.save()

        user = BaseUser.objects.get()
        self.assertEqual(user.slug, unique_slug)
        self.assertEqual(user.name, unique_slug)


class BaseUserEditionFormTest(TestCase):
    def setUp(self):
        self.user = BaseUserFactory()

    def test_base_user_edition_form__save(self):
        """Check that user got a new slug if name as changed."""
        old_name, old_slug = self.user.name, self.user.slug
        valid_form = BaseUserEditionForm({
            'name': 'Baptou',
            'email': self.user.email,
        }, instance=self.user)
        assert valid_form.is_valid()
        valid_form.save()

        assert not self.user.name == old_name
        self.assertNotEqual(self.user.slug, old_slug)

    def test_base_user_edition_form__save_small_avatar(self):
        # Create fake uploaded file
        f = get_test_picture()

        form_with_avatar = BaseUserEditionForm({
            'name': self.user.name,
            'email': self.user.email,
            '_avatar': f,
        }, instance=self.user)
        assert form_with_avatar.is_valid()

        self.assertIsNotNone(self.user._small_avatar)

    def test_base_user_edition_form__clean_name(self):
        """Check that form.change_name is set to true if name has been changed."""
        valid_form = BaseUserEditionForm({
            'name': 'Baptou',
            'email': self.user.email,
        }, instance=self.user)
        assert not hasattr(valid_form, 'change_name')
        assert valid_form.is_valid()

        self.assertTrue(hasattr(valid_form, 'change_name'))
        self.assertTrue(valid_form.change_name)

    def test_base_user_edition_form__clean__avatar_without_avatar(self):
        form_without_avatar = BaseUserEditionForm({}, {
            '_avatar': None
        }, instance=self.user)
        form_without_avatar.is_valid()

        self.assertIsNone(form_without_avatar.small_avatar)
        self.assertFalse(hasattr(form_without_avatar, 'small_avatar_ext'))

    def test_base_user_edition_form__clean__avatar_with_avatar(self):
        # Create fake uploaded file
        f = get_test_picture()

        form_with_avatar = BaseUserEditionForm({}, {
            '_avatar': f
        }, instance=self.user)
        form_with_avatar.is_valid()

        self.assertIsNotNone(form_with_avatar.small_avatar)
        self.assertTrue(hasattr(form_with_avatar, 'small_avatar_ext'))
        self.assertEqual(form_with_avatar.small_avatar_ext, 'png')

    @override_settings(MAX_UPLOAD_SIZE=4000)
    def test_base_user_edition_form__clean__avatar_too_big(self):
        # Create fake uploaded file
        f = get_test_picture()

        form_with_big_avatar = BaseUserEditionForm({}, {
            '_avatar': f
        }, instance=self.user)

        self.assertFalse(form_with_big_avatar.is_valid())
        self.assertIn(
            BaseUserEditionForm.error_messages['image_too_big'].format(file_size=filesizeformat(f._size)),
            form_with_big_avatar.errors.get('_avatar'))

class BaseUserDeleteFormTest(TestCase):
    def setUp(self):
        self.user = BaseUserFactory()

    def test_base_user_delete_form_is_valid(self):
        """Checks that user passed to form.is_valid is saved as user attribute on form."""
        form = BaseUserDeleteForm()
        assert not hasattr(form, 'user')
        form.is_valid(user=self.user)

        self.assertTrue(hasattr(form, 'user'))
        self.assertEqual(form.user, self.user)

    def test_base_user_delete_form_clean_password(self):
        field = 'password'

        bad_password_form = BaseUserDeleteForm({field: 'bad_password'})
        bad_password_form.is_valid(user=self.user)
        self.assertIn(field, bad_password_form.errors)
        self.assertIn(BaseUserDeleteForm.error_messages['invalid_password'], bad_password_form.errors.get(field))

        valid_password_form = BaseUserDeleteForm({field: 'password'})
        valid_password_form.is_valid(user=self.user)
        self.assertNotIn(field, valid_password_form.errors)
