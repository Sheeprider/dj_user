from any_imagefield.models import AnyImageField
from django.conf import settings
from django.db import models
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from storages.backends.s3boto import S3BotoStorage


# ########################################################
# S3FileField.py
# Extended FileField and ImageField for use with Django and Boto.
#
# Required settings:
#   AWS_BUCKET_NAME - String, represents the default bucket name to use if one isn't provided
#   AWS_ACCESS_KEY_ID - String
#   AWS_SECRET_ACCESS_KEY - String
#
# ########################################################

class S3EnabledFileField(models.FileField):
    def __init__(self, verbose_name=None, name=None, upload_to='', storage=None, **kwargs):
        storage = S3BotoStorage(bucket_name='ls-uploads')
        super(S3EnabledFileField, self).__init__(verbose_name, name, upload_to, storage, **kwargs)


class S3EnabledImageField(AnyImageField):
    allowed_extentions = ['.gif', '.jpeg', '.jpg', '.png']
    help_text = _(
        u'Allowed extensions: [{formats}], max size: [{size}]'.format(
            formats=', '.join(allowed_extentions), size=filesizeformat(settings.MAX_UPLOAD_SIZE))
    )

    def __init__(self, verbose_name=None, name=None, upload_to=None, **kwargs):
        kwargs['storage'] = kwargs.get('storage', S3BotoStorage(bucket_name=upload_to or settings.AWS_BUCKET_NAME))
        kwargs['help_text'] = kwargs.get('help_text') or self.help_text
        super(S3EnabledImageField, self).__init__(
            verbose_name=verbose_name,
            name=name,
            upload_to=upload_to,
            **kwargs)


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    # Enable south for S3EnabledFileField and S3EnabledImageField
    rules = [
        (
            (S3EnabledFileField, ),
            [],
            {
                "bucket": ["bucket"],
            },
        ),
    ]
    add_introspection_rules(rules, ["^commons\.S3FileField\.S3EnabledFileField"])
    add_introspection_rules([], ["^commons\.fields\.S3EnabledImageField"])
