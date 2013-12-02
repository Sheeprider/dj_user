import json

from django.core.files import File

from commons.tests.models import OtherModel1, OtherModel2, Model
from commons.tests.utils import TEST_PICTURE
from commons.tests.test_case import AbstractModelTest


class ModelModelTest(AbstractModelTest):

    def setUp(self):
        f = open(TEST_PICTURE)
        myfile = File(f)

        self.other1 = OtherModel1.objects.create(description='description')
        self.other2 = OtherModel2.objects.create()
        self.other2.other.add(self.other1)
        self.model = Model.objects.create(
            name='name',
            other=self.other1,
            _email='baptiste@smoothie-creative.com',
            _site='www.google.fr',
            _file=myfile)

    def test_to_dict__return_a_dict_of_attributes(self):
        model_to_dict = self.model.to_dict()

        self.assertIsInstance(model_to_dict, dict)
        self.assertIn('id', model_to_dict)
        self.assertIn('name', model_to_dict)

    def test_to_dict__properties_instead_of_underscored_attributes(self):
        model_to_dict = self.model.to_dict()

        self.assertIn('email', model_to_dict)
        self.assertNotIn('_email', model_to_dict)

    def test_to_dict__underscored_attribute_if_property_does_not_exist(self):
        model_to_dict = self.model.to_dict()

        self.assertIn('_site', model_to_dict)
        self.assertNotIn('site', model_to_dict)

    def test_to_dict__is_recursive(self):
        model_to_dict = self.model.to_dict()

        self.assertIn('other', model_to_dict)
        self.assertIn('description', model_to_dict['other'])

    # TODO : see commons.models TODO line 51 about modelsmanager conversion
    # def test_to_dict__recursivity_stops_on_same_model(self):
    #     model_to_dict = self.model.to_dict()

    #     self.assertIn('other2', model_to_dict['other'])
    #     self.assertNotIn('other', model_to_dict['other']['other2'])

    def test_to_dict__can_specify_fields_by_name(self):
        fields = ['name']
        model_to_dict = self.model.to_dict(fields=fields)

        self.assertEquals(model_to_dict.keys(), fields)

    def test_to_dict__can_exclude_fields_by_name(self):
        exclude = ['id']
        model_to_dict = self.model.to_dict(exclude=exclude)

        self.assertIn('name', model_to_dict)
        self.assertNotIn(exclude[0], model_to_dict)

    # TODO : see commons.models TODO line 51 about modelsmanager conversion
    # def test_to_dict__convert_related_managers(self):
    #     other2_to_dict = self.other2.to_dict()

    #     self.assertIn('other', other2_to_dict)
    #     self.assertIsInstance(other2_to_dict['other'], list)
    #     self.assertIsInstance(other2_to_dict['other'][0], dict)

    def test_to_dict__convert_models(self):
        model_to_dict = self.model.to_dict()

        self.assertIn('other', model_to_dict)
        self.assertIsInstance(model_to_dict['other'], dict)

    def test_to_dict__convert_files(self):
        model_to_dict = self.model.to_dict()

        self.assertIn('_file', model_to_dict)
        self.assertIsInstance(model_to_dict['_file'], basestring)
        self.assertEquals(self.model._file.url, model_to_dict['_file'])

    def test_to_dict__convert_dates(self):
        model_to_dict = self.model.to_dict()

        self.assertIn('today', model_to_dict)
        self.assertIsInstance(model_to_dict['today'], basestring)

    def test_to_dict__is_json_encodable(self):
        model_to_dict = self.model.to_dict()

        json_dict = json.dumps(model_to_dict)
        self.assertIsInstance(json_dict, basestring)
