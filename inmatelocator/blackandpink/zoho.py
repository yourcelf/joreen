# -*- coding: utf-8 -*-
import re
import json
import requests
import logging

from django.conf import settings

from stateparsers.request_caching import setup_cache

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

    setup_cache(name="cache/zoho")

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

    res = requests.get(url, params=payload)
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

    with requests_cache.disabled():
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

    with requests_cache.disabled():
        res = requests.post(url, data=payload)
    return {"status_code": res.status_code, "text": json.loads(res.text)}
