# -*- coding: utf-8 -*-
from django.test import TestCase

from user.models import UserManager, BaseUser


class UserManagerTest(TestCase):
# No subclasses distributed with this package
#     def test_select_subclasses(self):
#         """
#         Tests that Querystets return the right type of objects.
#         """
#         Student.objects.create_student("baptiste+1@smoothie-creative.com", "password", slug="baptiste_1", name="baptiste_1")
#         Teacher.objects.create_teacher("baptiste+2@smoothie-creative.com", "password", slug="baptiste_2", name="baptiste_2")

#         [self.assertIsInstance(user, Student) for user in BaseUser.objects.filter(student__isnull=False).select_subclasses("student").all()]
#         [self.assertIsInstance(user, Teacher) for user in BaseUser.objects.filter(teacher__isnull=False).select_subclasses("teacher").all()]

    def test_create_user(self):
        """Test user creation."""
        old_user_count = BaseUser.objects.count()
        user = BaseUser.objects.create_user("baptiste@smoothie-creative.com", "password", slug="baptiste", name="baptiste")
        self.assertIsInstance(user, BaseUser)
        self.assertEqual(BaseUser.objects.count(), old_user_count + 1)

    def test_create_superuser(self):
        """Test superuser creation."""
        old_user_count = BaseUser.objects.count()
        superuser = BaseUser.objects.create_superuser("baptiste@smoothie-creative.com", "password", slug="baptiste", name="baptiste")
        self.assertIsInstance(superuser, BaseUser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertEqual(BaseUser.objects.count(), old_user_count + 1)

    def test_user_manager(self):
        """Test user's manager."""
        self.assertIsInstance(BaseUser.objects, UserManager)
