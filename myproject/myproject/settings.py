# Otros import y configuraciones
from pathlib import Path
import os

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'myapp' / 'static',
]

# Ruta de la fuente personalizada
FONT_PATH = os.path.join(BASE_DIR, 'myapp', 'static', 'ASMAN.ttf')

# Configuraciones importantes
SECRET_KEY = 'django-insecure-o(ghtg5w*^_yxs_9ij9@7#ie7c(b%extdi!s=&^+iu(6*cwzp-'
DEBUG = True
ALLOWED_HOSTS = ['192.168.18.12', '127.0.0.1', 'localhost','stayhere-web.onrender.com']

INSTALLED_APPS = [
    'myapp',
    'rest_framework',
    'corsheaders',
    'captcha', #Inclusion de captcha
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'myapp/templates')],
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

WSGI_APPLICATION = 'myproject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'railway',
        'USER': 'root',
        'PASSWORD': 'oMLwIlTHnqxNzidWUCoMKXwXWrBUJKMk',
        'HOST': 'autorack.proxy.rlwy.net',
        'PORT': '25526',
    }
}

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

CORS_ALLOWED_ORIGINS = [
    'http://192.168.18.52',
    'http://192.168.18.12',
    'http://localhost:8000',
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Datos agregados para el correcto funcionamiento de:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'jaredalejandro.gb@gmail.com'
EMAIL_HOST_PASSWORD = 'xvil bplx cssm ozru'
DEFAULT_FROM_EMAIL = 'jaredalejandro.gb@gmail.com'

# LOGIN
AUTH_USER_MODEL = 'myapp.Usuario'

# Verificacion de inicio de sesion
LOGIN_URL = '/login/' 


# Cargo de imagenes
# settings.py

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CSRF_TRUSTED_ORIGINS = ['http://192.168.18.12:8000']
CSRF_COOKIE_SECURE = False
