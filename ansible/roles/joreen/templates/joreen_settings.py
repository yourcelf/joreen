from .default_settings import *

DEBUG = TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['{{django_domain}}']

ZOHO_APPLICATION_LINK_NAME = "prisoner-profiles"
ZOHO_PROFILE_VIEW_NAME = "Prisoner_Profiles_View"
ZOHO_PROFILE_FORM_NAME = "Prisoner_Profiles"
ZOHO_FACILITIES_VIEW_NAME = "Prison_Facilities_View"
ZOHO_FACILITIES_FORM_NAME = "Prison_Facilities"
ZOHO_AUTHENTICATION_TOKEN = "{{joreen_zoho_authentication_token}}"
ZOHO_OWNER_NAME = "reedmiller17"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '{{joreen_postgres_db}}',
        'USER': '{{joreen_postgres_user}}',
        'PASSWORD': '{{joreen_postgres_password}}'
    }
}

MOCK_ZOHO_UPDATES = False
