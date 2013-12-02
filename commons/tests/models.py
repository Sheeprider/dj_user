from django.db import models

from commons.models import Model as _Model


class OtherModel1(_Model):
    """Dummy model, to test Model abstract model."""
    description = models.TextField()

    class Meta:
        app_label = 'commons'


class Model(_Model):
    """Dummy model, to test Model abstract model."""
    name = models.CharField(max_length=10)
    other = models.ForeignKey(OtherModel1, related_name='model')
    today = models.DateField(auto_now=True)
    _file = models.FileField(upload_to='files')
    _email = models.CharField(max_length=30)
    _site = models.CharField(max_length=30)

    class Meta:
        app_label = 'commons'


    @property
    def email(self):
        return self._email


class OtherModel2(_Model):
    """Dummy model, to test Model abstract model."""
    other = models.ManyToManyField(OtherModel1, null=True, default=None, blank=True, related_name='other2')

    class Meta:
        app_label = 'commons'
