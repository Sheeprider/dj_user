import re

from any_imagefield.models import AnyImageField
from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.template.defaultfilters import filesizeformat
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from storages.backends.s3boto import S3BotoStorage


# ########################################################
# S3FileField.py
# Extended FileField and ImageField for use with Django and Boto.
#
# Required settings:
#   USE_AMAZON_S3 - Boolean, self explanatory
#   AWS_STORAGE_BUCKET - String, represents the default bucket name to use if one isn't provided
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
        kwargs['storage'] = kwargs.get('storage', S3BotoStorage(bucket_name=upload_to or settings.AWS_STORAGE_BUCKET))
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


class UrlWidget(forms.TextInput):
    def render(self, name, value, attrs=None):
        html = super(UrlWidget, self).render(name, value, attrs)
        splited_name = re.search('^(?P<base_name>.+_)(?P<id_>\d+)$', name)
        base_name = splited_name.group('base_name')
        id_ = splited_name.group('id_')
        html = mark_safe(u'<div class="js-sites-widget" data-group="%s" data-base-name="%s">%s<a href="#" class="removeField ss-standard-icon" data-widget-type="site">Delete</a><a href="#" class="addField ss-standard-icon" data-widget-type="site">Add</a></div>' % (id_, base_name, html))
        return html


class SiteWidget(forms.MultiWidget):
    uw = UrlWidget(attrs={'class': 'site-widget', 'placeholder': _('Entrer un site'), 'autocomplete': 'off'})

    def __init__(self, sites=[], *args, **kwargs):
        widgets = []
        for site in sites:
            widgets.append(self.uw)
        widgets.append(self.uw)
        super(SiteWidget, self).__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value and isinstance(value, Site):
            return [value.site]
        return [None]


class SiteField(forms.MultiValueField):
    uf = forms.URLField(max_length=255, )

    def __init__(self, *args, **kwargs):
        fields = []
        sites = kwargs.get('initial', [])
        for site in sites:
            fields.append(self.uf)
        fields.append(self.uf)
        super(SiteField, self).__init__(fields, *args, **kwargs)
        self.widget = SiteWidget(sites=sites)

    def compress(self, data_list):
        data_list = filter(None, data_list)
        return data_list
