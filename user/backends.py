# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.conf import settings
from facebook import GraphAPI, GraphAPIError
from storages.backends.s3boto import S3BotoStorage

# Create static files storages
StaticS3Storage = lambda: S3BotoStorage(bucket_name=settings.AWS_STATIC_BUCKET, location='static')


class FacebookBackend(object):
    """
    Authenticate against the Facebook account.

    Use the facebook token to verify the user on facebook.
    """
    def authenticate(self, fb_id=None, access_token=None):
        if not (fb_id and access_token):
            return None

        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get(_fb_id=fb_id)
        except UserModel.DoesNotExist:
            return None
        else:
            try:
                g = GraphAPI(access_token)
                g.get('me', {})
            except GraphAPIError:
                return None
            else:
                return user

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
