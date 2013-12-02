# -*- coding: utf-8 -*-
from random import choice
from string import digits
from StringIO import StringIO

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.text import slugify
from facebook import FacebookAPI
from PIL import Image


def unique_slugify(model_name, model, **other_attrs):
    slug = slugify(unicode(model_name))
    while model.objects.filter(slug=slug, **other_attrs).exists():
        # Add unique token
        slug += "_" + "".join(choice(digits) for i in range(5))
    return slug


def resize(img, (width, height), ext):
    """Resize an uploaded avatar, and return it as a StringIO."""
    expected_ratio = float(height) / float(width)
    if ext in (u'png', u'gif'):
        # Convert to rgba to keep transparency informations
        img = img.convert(u'RGBA')
    w, h = img.size
    ratio = float(h) / float(w)
    if ratio < expected_ratio:
        # Landscape, img is too wide
        # Resize img to have img.height = height and img.width > width
        img = img.resize((int(w * (float(height) / float(h))), height), Image.ANTIALIAS)
        # Crop ((img.width - width) / 2) on each side of img
        w, h = img.size
        left = (w - width) / 2
        right = left + width
        top = 0
        bottom = height
        img = img.crop((left, top, right, bottom))
        img.load()
    elif ratio > expected_ratio:
        # Portrait, img is too tall
        # Resize img to have img.width = width and img.height > height
        img = img.resize((width, int(h * (float(width) / float(w)))), Image.ANTIALIAS)
        # Crop ((img.height - height) / 2) at the top and the bottom of img
        w, h = img.size
        left = 0
        right = width
        top = (h - height) / 2
        bottom = top + height
        img = img.crop((left, top, right, bottom))
        img.load()
    else:
        # Good ratio, juste resize
        img.thumbnail((width, height), Image.ANTIALIAS)
    # save avatar to temp file
    tmp_avatar = StringIO()
    img.save(tmp_avatar, ext)
    tmp_avatar.seek(0)
    return tmp_avatar


def absolute_url(relative_url, https=False):
    SITE = Site.objects.get(pk=settings.SITE_ID)
    scheme = 'https://' if https else 'http://'
    return "".join((scheme, SITE.domain, relative_url))


def get_facebook():
    return FacebookAPI(
        client_id=settings.FACEBOOK_APP_ID,
        client_secret=settings.FACEBOOK_APP_SECRET,
        redirect_uri=absolute_url(reverse('user:fb.callback')))


def clean_fb_session(session):
    if session.get('fb_token'):
        del session['fb_token']
    if session.get('fb_id'):
        del session['fb_id']
