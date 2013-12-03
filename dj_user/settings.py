"""
Django settings for dj_user project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '4(cc^lw^dkd60mlu&%s-li$%=_wwoq#7pv#4fqj34l=-&lcgn7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    #
    'django_nose',
    'commons',
    'user',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'dj_user.urls'

WSGI_APPLICATION = 'dj_user.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

#  =================
#  = user settings =
#  =================
if not DEBUG:
    TEMPLATE_LOADERS = ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),

SITE_ID = 1
LOGIN_URL = 'user:login'
LOGIN_REDIRECT_URL = 'user:home'
# Define a custom user model
AUTH_USER_MODEL = 'user.BaseUser'

#  ==========
#  = Amazon =
#  ==========
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_KEY')
AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
AWS_STATIC_BUCKET = AWS_BUCKET_NAME
if not DEBUG:
    # =====================================
    # = Upload static files to S3 on prod =
    # =====================================
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    STATICFILES_STORAGE = 'user.backends.StaticS3Storage'

#  ==========
#  = Upload =
#  ==========
AWS_UPLOAD_BUCKET = AWS_BUCKET_NAME
MAX_UPLOAD_SIZE = 2621440  # 2.5 MB
AVATAR_SIZE = 160, 200
AVATAR_SMALLSIZE = 40, 50

#  ============
#  = Facebook =
#  ============
FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET')
from django.conf.global_settings import AUTHENTICATION_BACKENDS as AB
AUTHENTICATION_BACKENDS = AB + (
    'user.backends.FacebookBackend',
)

#  ===============
#  = Test runner =
#  ===============
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_PLUGINS = (
    'commons.cover.Coverage',
)
NOSE_ARGS = (
    # "--processes=-1",
    # "--with-stopwatch",
    # py -c "import pickle, pprint;e_time = pickle.load( open( '.nose-stopwatch-times', 'rb' ) );pprint.pprint(e_time, indent=4);exit();"
    "--logging-filter=-south,-factory",
    # "--collect-only",
    # "--cover-branches",
    # "--with-coverage",
    # "--cover-min-percentage=90",
    "--cover-erase",
    "--cover-html",
    "--cover-html-dir=htmlcov",
    "--cover-tests",
    # "--cover-branches",
    # "--cover-inclusive",
    "--cover-omit=env/*",
    "--cover-omit=*/migrations/*",
    # "--cover-omit=manage.py",
    # TODO : Find where they are, and kill them.
    # SEE : https://docs.djangoproject.com/en/dev/topics/testing/advanced/#integration-with-coverage-py
    "--cover-omit=*FixTk*",
    "--cover-omit=*LWPCookieJar*",
    "--cover-omit=*_MozillaCookieJar*",
    "--cover-omit=*cookielib*",
    "--cover-omit=*encodings*",
    "--cover-omit=*getpass*",
    "--cover-omit=*httplib*",
    "--cover-omit=*netrc*",
    "--cover-omit=*shlex*",
    "--cover-omit=*smtplib*",
    "--cover-omit=*stringprep*",
    "--cover-omit=*urllib2*",
    "--cover-omit=*xml*",
    "--cover-omit=*ctypes*",
    "--cover-omit=*uuid*",
)
