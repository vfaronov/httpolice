SECRET_KEY = 'hco(z9+1=c(hx94+mr@jn1&xw6)%_$f131t_)o8q)t)tw=%d+i'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = ['example_app']

MIDDLEWARE_CLASSES = [
    'django_httpolice.HTTPoliceMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'example_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]

LANGUAGE_CODE = 'en-us'
USE_I18N = False
USE_L10N = False
TIME_ZONE = 'UTC'
USE_TZ = True

HTTPOLICE_ENABLE = True
HTTPOLICE_RAISE = True
