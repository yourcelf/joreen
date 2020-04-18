# This is a set of convenience imports for use inside the django shell.  To
# pull in most of the Django world and other things you might need inside the
# Django shell, call:
#
#  >>> from sh import *
#

# flake8: noqa

import re
from imp import reload
from collections import Counter

from django.conf import settings
from django.utils.timezone import now
from django.utils import timezone
from django.contrib.auth.models import *

from facilities.models import *
from stateparsers.models import *
from stateparsers import AVAILABLE_STATES, get_searcher, search
from blackandpink.models import *
from blackandpink import zoho
from blackandpink.blackandpink import Address, Profile
import blackandpink.blackandpink as bp

import usaddress
import probablepeople


def get_zoho_address(name):
    data = zoho.fetch_all_facilities()
    for d in data:
        if d["Address_1_Facility"] == name:
            return Address.from_zoho(d)
    raise Exception("Not found")


def get_facility_address(name=None, **kwargs):
    if name:
        f = Facility.objects.get(name=name)
    else:
        f = Facility.objects.get(**kwargs)
    return Address.from_facility(f)
