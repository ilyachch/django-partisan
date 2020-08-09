import multiprocessing as mp
import os

SECRET_KEY = 'fake-key'

DEBUG = True

INSTALLED_APPS = [
    'django_partisan',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

if bool(os.getenv('LOG_SQL', False)):
    LOGGING = {
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'level': 'DEBUG',
            },
        },
        'root': {
            'handlers': ['console'],
        }
    }

MIN_QUEUE_SIZE = 2
MAX_QUEUE_SIZE = 10
CHECKS_BEFORE_CLEANUP = 50
WORKERS_COUNT = mp.cpu_count()
SLEEP_DELAY_SECONDS = 2
TASKS_PER_WORKER_INSTANCE = None
DELETE_TASKS_ON_COMPLETE = False

print(os.environ)

if not os.getenv('CHECK_MYPY'):
    from .test_settings import *
