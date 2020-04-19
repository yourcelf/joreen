from .dev_settings import *  # noqa: F401,F403

ZOHO_APPLICATION_LINK_NAME = "..."
ZOHO_PROFILE_VIEW_NAME = "..."
ZOHO_PROFILE_FORM_NAME = "..."
ZOHO_FACILITIES_VIEW_NAME = "..."
ZOHO_FACILITIES_FORM_NAME = "..."
ZOHO_AUTHENTICATION_TOKEN = "..."
ZOHO_OWNER_NAME = "..."

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "inmatelocator",
        "USER": "inmatelocator",
        "PASSWORD": "inmatelocator",
    }
}
