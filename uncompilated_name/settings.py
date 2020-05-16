"""
Django settings for uncompilated_name project.

Generated by 'django-admin startproject' using Django 3.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'y4f7a3!kr07u!jem=#1dm@pj@lgm#16#!=)3_m6@@+5k_+mz$c'

# SECURITY WARNING: don't run with debug turned on in production!


if os.environ.get('ENV') == 'PRODUCTION':
    DEBUG = False
else :
    DEBUG = True



ALLOWED_HOSTS = ['uncompilatedname.herokuapp.com','localhost']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chatbot'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'uncompilated_name.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR,'templates'),
        ],
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

WSGI_APPLICATION = 'uncompilated_name.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
if os.environ.get('ENV') == 'PRODUCTION':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',   # Backends disponibles : 'postgresql', 'mysql', 'sqlite3' et 'oracle'.
            'NAME': 'da2iau4ctgkned',             # Nom de la base de données
            'USER': 'kfrmjzmfzabgoj',
            'PASSWORD': '3c968e6ea4157990fe88a0b6d9bb7936922fb5d4668cad58d05773adc17d0eec',        
            'HOST': 'ec2-52-201-55-4.compute-1.amazonaws.com',                    # Utile si votre base de données est sur une autre machine
            'PORT': '5432',                          #... et si elle utilise un autre port que celui par défaut
        }
    }

else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',   # Backends disponibles : 'postgresql', 'mysql', 'sqlite3' et 'oracle'.
            'NAME': 'un',             # Nom de la base de données
            'USER': 'root',
            'PASSWORD': '',        
            'HOST': '127.0.0.1',                    # Utile si votre base de données est sur une autre machine
            'PORT': '3306',                          #... et si elle utilise un autre port que celui par défaut
            'TEST': {
                'CHARSET' : 'utf8',
                'COLLATION':'utf8_general_ci'
            }
        }
    }

"""DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',   # Backends disponibles : 'postgresql', 'mysql', 'sqlite3' et 'oracle'.
        'NAME': 'un',             # Nom de la base de données
        'USER': 'postgres',
        'PASSWORD': 'Bejaia06',        
        'HOST': '127.0.0.1',                    # Utile si votre base de données est sur une autre machine
        'PORT': '5432',                          #... et si elle utilise un autre port que celui par défaut
        'TEST': {
            'CHARSET' : 'utf8',
            'COLLATION':'utf8_general_ci'
        }
    }
}"""


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'fr-FR'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
if os.environ.get('ENV') == 'PRODUCTION':
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
