from datetime import datetime, date, time, timedelta

from django.db import models
from django.db.models.manager import Manager
from django.db.models.fields.files import FieldFile

def get_attr(obj, _attribute):
    """
    Return a 2-tupple with _attribute name and _attribute value from obj.
    If attribute exists on obj it is used instead.
    """
    attribute = _attribute
    if attribute.startswith('_'):
        attribute = attribute[1:]
    if hasattr(obj, attribute):
        return (attribute, getattr(obj, attribute))
    return (_attribute, getattr(obj, _attribute))


class Model(models.Model):
    class Meta:
        abstract = True

    def to_dict(self, fields=None, exclude=None, chain=None):
        """
        Recursively inspect fields to produce a json-encodable dict
        representing this model.
        """
        # Remember all inspected models to avoid infinite recursion
        if not chain:
            chain = []
        stop = self in chain
        chain.append(self)

        # Get all field names or a specified subset of it
        all_fields = set(self._meta.get_all_field_names())
        fields = set(fields) & all_fields if fields else all_fields
        exclude = set(exclude) & all_fields if exclude else set()
        fields -= exclude

        # Basic dict of field_names: field_values
        _dict = dict(get_attr(self, field) for field in fields if hasattr(self, field))

        #  ==================
        #  = Post treatment =
        #  ==================
        # Convert related_managers to a list of dicts of models
        related_managers = dict((name, field) for name, field in _dict.iteritems() if isinstance(field, Manager))
        while related_managers:
            name, manager = related_managers.popitem()
            # TODO : either find a faster way to get related models, or don't recurse on managers.
            # _dict[name] = [obj.to_dict(chain=chain) for obj in manager.all() if not obj in chain]
            # if not manager.count() == len(_dict[name]):
            #     del _dict[name]
            del _dict[name]

        # Convert models to their dict versions
        models_ = dict((name, field) for name, field in _dict.iteritems() if isinstance(field, models.Model))
        while models_:
            name, model = models_.popitem()
            if not stop:
                _dict[name] = model.to_dict(chain=chain)
            else:
                # Stop recursion
                del _dict[name]

        # Replace files by their urls
        files = dict((name, file_.url if file_ else None) for name, file_ in _dict.iteritems() if isinstance(file_, FieldFile))
        # files = dict((name, file_.url if file_ else None) for name, file_ in files.iteritems())
        _dict.update(files)

        # Convert dates to strings
        dates = dict((name, str(date_)) for name, date_ in _dict.iteritems() if isinstance(date_, (datetime, date, time, timedelta)))
        # dates = dict((name, str(date)) for name, date in dates.iteritems())
        _dict.update(dates)

        return _dict
