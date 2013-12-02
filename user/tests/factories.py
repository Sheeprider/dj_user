import factory

from django.utils.text import slugify
from django.contrib.auth.hashers import make_password

from user import models


class BaseUserFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.BaseUser

    name = factory.Sequence(lambda n: u'User %d' % n)
    slug = factory.LazyAttribute(lambda a: slugify(unicode(a.name)))
    email = factory.LazyAttribute(lambda a: '{0}@example.com'.format(a.slug))
    password = factory.LazyAttribute(lambda a: make_password("password"))
