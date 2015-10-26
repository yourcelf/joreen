# -*- coding: utf-8 -*-
import os
import json
import time
import requests

from stateparsers.states import LookupResult
from facilities.models import Facility

def search(**kwargs):
    url = "http://www.bop.gov/PublicInfo/execute/inmateloc"

    searches = []
    if kwargs.get('number'):
        for numtype in ("IRN", "DCDC", "FBI", "INS"):
            searches.append({"inmateNum": kwargs['number'], "inmateNumType": numtype})
    else:
        searches.append({"nameFirst": kwargs.get("first_name"), "nameLast": kwargs.get("last_name")})

    results = []
    errors = []

    for i,search in enumerate(searches):
        search['todo'] = 'query'
        search['output'] = 'json'
        res = requests.get(url, params=search)
        if res.status_code != 200:
            errors.append(res.content)
            break

        data = json.loads(res.content)
        if 'InmateLocator' not in data:
            errors.append(res.content)
            continue
        for entry in data['InmateLocator']:
            if entry['releaseCode'] == "R":
                status = LookupResult.STATUS_RELEASED 
                facilities = None
            elif entry['faclCode'] == "":
                status = LookupResult.STATUS_UNKNOWN
                facilities = None
            else:
                status = LookupResult.STATUS_INCARCERATED
                facilities = Facility.objects.filter(
                    administrator__name="Federal Bureau of Prisons",
                    code=entry['faclCode']
                )

            result = LookupResult(
                name=u"{} {}".format(entry.pop('nameFirst'), entry.pop('nameLast')),
                status=status,
                numbers={entry.pop('inmateNumType'): entry.pop('inmateNum')},
                facilities=facilities,
                search_url=url,
                result_url=None,
                extra=entry
            )
            results.append(result)

    return {"state": "Federal", "results": results, "errors": errors, "url": url}

