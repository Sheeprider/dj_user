#Django base user app

This app (user) can be used in any django project which require a custom django user model.

All credential settings will be taken from env by default.
The following settings are available / required :

- AWS_ACCESS_KEY_ID : String. (None)
- AWS_SECRET_ACCESS_KEY : String. (None)
- AWS_BUCKET_NAME : String, represents the default bucket name to use if one isn't provided. (None)
- AWS_UPLOAD_BUCKET : String, represents the bucket name to use for uploads. (AWS_BUCKET_NAME)
- AWS_STATIC_BUCKET : String, represents the bucket name to use for collectstatic. (AWS_BUCKET_NAME)
- MAX_UPLOAD_SIZE : Int, maximum upload size, in bytes. (2.5 MB)
- AVATAR_SIZE : Tuple (Int, Int), dimentions to use for avatar resizing/croping. (160, 200)
- AVATAR_SMALLSIZE : Tuple (Int, Int), dimentions to use for small avatar resizing/croping. (40, 50)

**To serve staticfiles from S3 :**

- if not DEBUG:
-     STATIC_URL : String, base url of your bucket. (None)
-     DEFAULT_FILE_STORAGE : String, class to use as storage backend for Django. ('storages.backends.s3boto.S3BotoStorage')
-     STATICFILES_STORAGE : String, class to use as storage backend for static files. ('user.backends.StaticS3Storage')

**Login url, custom user class :**

- LOGIN_URL : String. ('user:login')
- LOGIN_REDIRECT_URL : String. ('user:home')
- AUTH_USER_MODEL : String. ('user.BaseUser')

**Facebook credentials** *You need a facebook app to connect your users to Facebook* :

- FACEBOOK_APP_ID : String. (None)
- FACEBOOK_APP_SECRET : String. (None)
- AUTHENTICATION_BACKENDS : Tuple, of authentication backends to use. (Django defaults + 'user.backends.FacebookBackend')

**Test settings :**

- SITE_ID : Int. (1)
- TEST_RUNNER : String. ('django_nose.NoseTestSuiteRunner')
- NOSE_PLUGINS : Tuple. ('commons.cover.Coverage',)
- NOSE_ARGS : Tuple, filter south and factory-boy from logging during tests and add coverage options by default.(see dj_user/settings.py)
