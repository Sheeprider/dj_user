# -*- coding: utf-8 -*-
import simplejson as json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from facebook import GraphAPI, GraphAPIError
from model_utils.managers import InheritanceManager

from commons.fields import S3EnabledImageField
from commons.models import Model


# Lazily return the user model to avoid inheritence problems.
_lazy_user_model = lambda *args, **kwargs: get_user_model()(*args, **kwargs)


class UserManager(InheritanceManager, BaseUserManager):
    """Custom user manager class."""

    @classmethod
    def create_user(self, email, password, _class=_lazy_user_model, **kwargs):
        """Create a user with specified parameters."""
        email = self.normalize_email(email)
        password = make_password(password)

        user = _class(email=email, password=password, **kwargs)
        user.save()
        return user

    @classmethod
    def create_superuser(self, email, password, **kwargs):
        return self.create_user(
            email,
            password,
            is_staff=True,
            is_superuser=True,
            **kwargs)

    def get_query_set(self):
        return super(UserManager, self).get_query_set().select_subclasses()


class BaseUser(Model, AbstractBaseUser, PermissionsMixin):
    """Custom user class."""
    email = models.EmailField(max_length=60, unique=True, db_index=True)
    is_active = models.BooleanField(_('active account'), default=True)
    is_staff = models.BooleanField(_('staff member'), default=False)
    created_at = models.DateTimeField(_('created at'), default=now())
    slug = models.CharField(max_length=130, unique=True)
    # Editable profile
    name = models.CharField(_('name'), max_length=120)
    _fb_token = models.CharField(_('facebook token'), default=None, blank=True, null=True, max_length=300)
    _fb_id = models.PositiveIntegerField(_('facebook id'), default=None, blank=True, null=True, max_length=15)

    _avatar = S3EnabledImageField(_('avatar'), upload_to=settings.UPLOAD_BUCKET, null=True, max_length=300, default=None, blank=True)
    _small_avatar = S3EnabledImageField(_('avatar (small)'), upload_to=settings.UPLOAD_BUCKET, null=True, max_length=300, default=None, blank=True)

    USERNAME_FIELD = 'email'

    objects = UserManager()

    def __repr__(self):
        return "<{0}: {1}>".format(self.__class__.__name__, self.email)

    def __str__(self):
        return str(self.email)

    def _get_name(self):
        """Return self.name as both long and short name."""
        return self.name

    def get_full_name(self):
        return self._get_name()

    def get_short_name(self):
        return self._get_name()

    @property
    def avatar(self):
        """Return User's avatar's url."""
        avatar = None
        if self._avatar:
            avatar = self._avatar.url
        return avatar

    @property
    def small_avatar(self):
        """Return User's small avatar's url."""
        avatar = None
        if self._small_avatar and self._avatar:
            avatar = self._small_avatar.url
        return avatar

    @property
    def fb_token(self):
        """Return facebook informations as dict."""
        if self._fb_token:
            return json.loads(self._fb_token)
        return self._fb_token

    @fb_token.setter
    def fb_token(self, fb_token):
        """Save facebook informations as a string."""
        if fb_token:
            fb_token = dict(fb_token)
            self._fb_token = json.dumps(fb_token)
        else:
            self._fb_token = None

    @property
    def fb_id(self):
        return self._fb_id

    @fb_id.setter
    def fb_id(self, fb_id):
        """Save fb_id as int."""
        if fb_id:
            if BaseUser.objects.filter(_fb_id=fb_id).exists():
                raise ValidationError(_('An user is already associated with this facebook account'))
            self._fb_id = int(fb_id, 10)
        else:
            self._fb_id = None

    def fb_is_connected(self):
        """
        Check if this user is connected to a Facebook account.
        Does not check the autorizations are still correct.
        """
        return self.fb_id and self.fb_token

    def fb_avatar(self):
        if not self.fb_is_connected():
            return None
        json_token = self.fb_token
        access_token = json_token.get(_('access_token'))
        try:
            # TODO : manage invalid/expired token (is this enough?)
            g = GraphAPI(access_token)
            data = g.get('me/picture', params={'redirect': 'false', })
        except GraphAPIError:
            return None

        avatar = data.get(_('data').get('url'))
        return avatar
