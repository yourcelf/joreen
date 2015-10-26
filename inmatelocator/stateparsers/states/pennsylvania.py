import re
import requests
import lxml.html

from stateparsers.states import LookupResult
from facilities.models import Facility

def search(**kwargs):
    url = "http://inmatelocator.cor.state.pa.us/inmatelocatorweb/"

    # Get the session cookie.
    sess = requests.Session()
    res = sess.get(url)
    root = lxml.html.fromstring(res.text)
    
    data = {
        'txtLstNm': kwargs.get("last_name"),
        'txtFrstNm': kwargs.get("first_name"),
        'txtMidNm': '',
        'txtInmNo': kwargs.get("number"),
        'cboSex': '---',
        'cboRace': '---',
        'cboCommCnty': '---',
        'cboLocation': '---',
        'cboCitizenship': '---',
        'grpAgeDOB': 'radDOB',
        'txtDobAge': '',
        'radList': 'radNam',
        'btnSearch': 'Find+Inmate'
    }

    for key in ("__EVENTVALIDATION", "__VIEWSTATE", "__VIEWSTATEGENERATOR",
                "__EVENTTARGET", "__EVENTARGUMENT"):
        data[key] = "".join(root.xpath('//input[@id="{}"/@value'.format(key))) 

    res = sess.post(url, data)
    root = lxml.html.fromstring(res.text)
    rows = root.xpath("//tr[@class='clstdfield']")
    results = []
    errors = []
    for row in rows:
        number, first_name, middle_name, last_name, suffix, race, dob, current_location, committing_county = row.xpath('./td//text()')

        name = " ".join((n for n in (first_name, middle_name, last_name) if n))
        if suffix:
            name = "{}, {}".format(name, suffix)

        result = LookupResult(
            name=name,
            numbers={"": number},
            search_url=url,
            result_url=None,
            facilities=Facility.fuzzy_lookup(
                term=normalize_facility_name(current_location),
                administrator__name="Pennsylvania"),
            extra=dict(
                race=race,
                date_of_birth=dob,
                current_location=current_location,
                committing_county=committing_county
            )
        )
        results.append(result)

    return {'state': 'Pennsylvania', 'results': results, 'errors': errors, 'url': url}




