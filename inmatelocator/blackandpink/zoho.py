# -*- coding: utf-8 -*-
import re
import json
import requests
import logging
from collections import defaultdict

from django.conf import settings
from django.utils import timezone

from stateparsers.request_caching import get_caching_session

def fetch_all_profiles(criteria=None):
    return fetch_all(settings.ZOHO_PROFILE_VIEW_NAME, criteria)

def fetch_all_facilities(criteria=None):
    return fetch_all(settings.ZOHO_FACILITIES_VIEW_NAME, criteria)

def fetch_all(view_link_name, criteria=None):
    """
    Zoho doesn't give us an efficient way to query filtering by a related value
    (e.g. "Facility.State", so rather than filter by state, just get
    *everything*; all 8500+ records.  Be sure to cache requests so this doesn't
    get out of hand if it re-runs.
    """

    session = get_caching_session(cache_name="cache/zoho")

    url = "https://creator.zoho.com/api/json/{application_link_name}/view/{view_link_name}"
    url = url.format(
        application_link_name=settings.ZOHO_APPLICATION_LINK_NAME,
        view_link_name=view_link_name,
    )
    payload = {
        "authtoken": settings.ZOHO_AUTHENTICATION_TOKEN,
        "scope": "creatorapi",
        "zc_ownername": settings.ZOHO_OWNER_NAME,
        "raw": "true",
    }
    if criteria:
        payload["criteria"] = criteria 

    res = session.get(url, params=payload)
    if res.status_code != 200:
        raise Exception("Status code {}, {}, {}".format(res.status_code, url, payload))

    text = res.text

    while True:
        try:
            data = json.loads(text)
            break
        except Exception as e:
            try:
                unexp = int(re.findall(r'\(char (\d+)\)', str(e))[0])
            except IndexError:
                raise e
            logging.warn(e)
            unesc = text.rfind(r'"', 0, unexp)
            logging.warn(text[unesc-20:unesc+20])
            text = text[:unesc] + r'\"' + text[unesc+1:]

    data = json.loads(text)
    return list(data.values())[0]

def add_facility(facility):
    admin = facility.administrator
    if admin and admin.name == "Federal Bureau of Prisons":
        address_type = "Federal"
    else:
        address_type = "State"
    result = insert_row(
        settings.ZOHO_FACILITIES_VIEW_NAME,
        settings.ZOHO_FACILITIES_FORM_NAME,
        {
            'Address_1_Facility': facility.name,
            'Address_2': facility.address1,
            'Address_3': facility.address2 or '',
            'Facility_Type': address_type,
            'City': facility.city,
            'State': facility.state,
            'Zip': facility.zip
        }
    )
    zoho_facility_id = result['text']['formname'][1]['operation'][1]['values']['ID']
    return fetch_all_facilities(criteria='ID={}'.format(zoho_facility_id))[0]

def update_profile(update_url, zoho_profile_id, address_status, release_status=None, zoho_facility_key=None):
    params = {
        "ID": zoho_profile_id,
        "Address_Status": address_status,
        "Autoupdater": "{}: {}".format(timezone.now().isoformat(), update_url)
    }
    if release_status:
        params['Status'] = release_status

    if zoho_facility_key:
        params['Facility'] = zoho_facility_key
    result = update_row(
        settings.ZOHO_PROFILE_VIEW_NAME,
        settings.ZOHO_PROFILE_FORM_NAME,
        params
    )
    return fetch_all_profiles(criteria='ID=={}'.format(zoho_profile_id))

def update_row(view_link_name, form_name, params):
    """
    Docs: https://www.zoho.com/creator/help/api/rest-api/rest-api-edit-records.html
    """
    shared_url = "https://creator.zoho.com/api/{ownername}/{format}/{applicationName}/view/{viewName}/record/update/"
    url = shared_url.format(
        format="json",
        ownername=settings.ZOHO_OWNER_NAME,
        applicationName=settings.ZOHO_APPLICATION_LINK_NAME,
        viewName=view_link_name,
        formName=form_name
    )
    payload = {
        "authtoken": settings.ZOHO_AUTHENTICATION_TOKEN,
        "scope": "creatorapi",
        "criteria": "ID=={}".format(params.pop('ID')),
        "formname": form_name,
    }
    payload.update(params)

    if settings.MOCK_ZOHO_UPDATES:
        print("UPDATE", payload)
        return {
            "status_code": 200,
            "text": {'formname': ['', {'operation': ['update', {'values': {}}]}]}
        }
    else:
        res = requests.post(url, data=payload)
        return {"status_code": res.status_code, "text": json.loads(res.text)}

def insert_row(view_link_name, form_name, params):
    url = "https://creator.zoho.com/api/{ownername}/{format}/{applicationName}/form/{formName}/record/add/".format(
        format="json",
        ownername=settings.ZOHO_OWNER_NAME,
        applicationName=settings.ZOHO_APPLICATION_LINK_NAME,
        viewName=view_link_name,
        formName=form_name
    )
    
    payload = {
        "authtoken": settings.ZOHO_AUTHENTICATION_TOKEN,
        "scope": "creatorapi",
    }
    payload.update(params)

    if settings.MOCK_ZOHO_UPDATES:
        print("INSERT", payload)
        return {'status_code': 200, 'text': {
            'formname': ['Prison_Facilities', {
                'operation': ['add', {
                    'status': 'Success',
                    'values': {
                        'Address_1_Facility': 'Test Facility',
                        'Address_2': '123 Nowhere St',
                        'City': 'Bozeman',
                        'Facility_Type': '**Personal Address**',
                        'ID': 1118888000004050003,
                        'State': 'MT',
                        'Zip': '59715'
                    }
                    }]
                }]
        }}
    else:
        res = requests.post(url, data=payload)
        return {"status_code": res.status_code, "text": json.loads(res.text)}
