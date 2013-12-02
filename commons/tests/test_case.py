import logging

from django.core.management.color import no_style
from django.db import models as dj_models, router, transaction, connections, DatabaseError
from django.test import TestCase
from django.utils.datastructures import SortedDict

logger = logging.getLogger('commons.tests.test_case.AbstractModelTest')


class AbstractModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Create the tables manually as neither Django nor Django-nose
        are capable of creating tables for test-only models.

        Inspired from: http://michael.mior.ca/2012/01/14/unit-testing-django-model-mixins/
        Code taken from django.core.management.commands.syncdb .
        """
        # Create the schema for our test model
        cls.db = 'default'
        cls.connection = connections[cls.db]
        cursor = cls.connection.cursor()
        tables = cls.connection.introspection.table_names()
        seen_models = cls.connection.introspection.installed_models(tables)

        cls.style = no_style()

        cls.created_models = set()
        pending_references = {}

        # Build the manifest of apps and models that are to be synchronized
        all_models = [
            (app.__name__.split('.')[-2],
                [m for m in dj_models.get_models(app, include_auto_created=True)
                if router.allow_syncdb(cls.db, m)])
            for app in dj_models.get_apps()
        ]

        def model_installed(model):
            opts = model._meta
            converter = cls.connection.introspection.table_name_converter
            return not ((converter(opts.db_table) in tables) or
                (opts.auto_created and converter(opts.auto_created._meta.db_table) in tables))

        manifest = SortedDict(
            (app_name, list(filter(model_installed, model_list)))
            for app_name, model_list in all_models
        )

        # Create the tables for each model
        for app_name, model_list in manifest.items():
            for model in model_list:
                # Create the model's database table, if it doesn't already exist.
                sql, references = cls.connection.creation.sql_create_model(model, cls.style, seen_models)
                seen_models.add(model)
                cls.created_models.add(model)
                for refto, refs in references.items():
                    pending_references.setdefault(refto, []).extend(refs)
                    if refto in seen_models:
                        sql.extend(cls.connection.creation.sql_for_pending_references(refto, cls.style, pending_references))
                sql.extend(cls.connection.creation.sql_for_pending_references(model, cls.style, pending_references))
                for statement in sql:
                    cursor.execute(statement)
                tables.append(cls.connection.introspection.table_name_converter(model._meta.db_table))

        transaction.commit_unless_managed(using=cls.db)

    @classmethod
    def tearDownClass(cls):
        #Remove test models from databases
        cursor = cls.connection.cursor()

        # Figure out which tables already exist
        table_names = cls.connection.introspection.table_names(cursor)

        sql = []

        # Output DROP TABLE statements for standard application tables.
        to_delete = set()

        for model in cls.created_models:
            if cursor and cls.connection.introspection.table_name_converter(model._meta.db_table) in table_names:
                to_delete.add(model)
                sql.extend(cls.connection.creation.sql_destroy_model(model, (), cls.style))

        # Execute queries
        sql = list(reversed(sql))
        for statement  in sql:
            # Drop tables using CASCADE.
            statement = statement[:-1] + " CASCADE" + statement[-1:]
            try:
                cursor.execute(statement)
                logger.debug("\n\tExecute statement: '{0}'.".format(statement))
            except DatabaseError, e:
                logger.error("\n\tStatement: '{0}'\n\tfailed with error: '{1}'.".format(statement, e))
                transaction.rollback()


        table_names = set(cls.connection.introspection.table_names(cursor))
        assert not to_delete & table_names
        assert not set(cls.created_models) & table_names

        # Close connection
        if cursor:
            cursor.close()
            cls.connection.close()
