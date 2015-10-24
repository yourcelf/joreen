import re
import time
import requests
import lxml.html

from localflavor.us.us_states import STATES_NORMALIZED

from states import LookupResult
from facilities.models import Facility

def search(**kwargs):
    url = "http://inmatelocator.cdcr.ca.gov/search.aspx"
    
    # Get the session cookie.
    sess = requests.Session()
    res = sess.get(url)
    root = lxml.html.fromstring(res.text)
    data = {
        "__EVENTVALIDATION": "".join(root.xpath('//input[@id="__EVENTVALIDATION"]/@value')),
        '__VIEWSTATE': ''.join(root.xpath('//input[@id="__VIEWSTATE"]/@value')),
        '__EVENTTARGET': "",
        '__EVENTARGUMENT': "",
        'text': ''.join(root.xpath('//textarea[@name="text"]/text()')),
        "ctl00$LocatorPublicPageContent$btnAccept": "Agree",
    }
    time.sleep(1)
    sess.post("http://inmatelocator.cdcr.ca.gov/default.aspx", data)

    # Now do the search
    time.sleep(1)
    res = sess.get(url)
    root = lxml.html.fromstring(res.text)
    query = {
        "ctl00$LocatorPublicPageContent$txtLastName": kwargs.get("last_name", ""),
        "ctl00$LocatorPublicPageContent$txtFirstName": kwargs.get("first_name", ""),
        "ctl00$LocatorPublicPageContent$txtCDCNumber": kwargs.get("number", ""),
        "ctl00$LocatorPublicPageContent$txtMiddleName": "",
        "ctl00$LocatorPublicPageContent$btnSearch": "Search",
        "__LASTFOCUS": "",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__EVENTVALIDATION": ''.join(root.xpath('//input[@id="__EVENTVALIDATION"]/@value')),
        "__VIEWSTATE": ''.join(root.xpath('//input[@id="__VIEWSTATE"]/@value')),

    }
    time.sleep(1)
    res = sess.post(url, query)

    # Now parse the results.
    root = lxml.html.fromstring(res.text)
    rows = root.xpath('//table[@id="ctl00_LocatorPublicPageContent_gvGridView"]//tr')
    results = []
    errors = []
    for row in rows:
        if len(row.xpath('./td')) == 0:
            continue
        name = "".join(row.xpath('(./td)[1]/text()'))
        if not name:
            text = u''.join(row.xpath('//text()')).strip()
            if "Next Page" in text or "Previous Page" in text or re.search("Page \d+ of \d+", text):
                continue
            else:
                errors.append(text)
                continue

        result = LookupResult(
            name=name,
            status=LookupResult.STATUS_INCARCERATED,
            numbers={"CDCR": "".join(row.xpath('(./td)[2]/text()'))},
            search_url=url,
            result_url=None,
            facilities=None,
            extra=dict(
                age="".join(row.xpath('(./td)[3]/text()')),
                admission_date=''.join(row.xpath('(./td)[4]/text()')),
                current_location=''.join(row.xpath('(./td)[5]/a/text()')),
                current_location_url=''.join(row.xpath('(./td)[5]/a/@href')),
                map_url=''.join(row.xpath('(./td)[6]/a/@href')),
            )
        )

        # Try to find facility matches.
        match = re.search("/Facilities_Locator/({\w+}).html", result.current_location_url)
        if match:
            result.facilities = Facility.objects.filter(code=match.group(1))
        elif "CA_Out_Of_State" in result.current_location_url and " - " in result.current_location:
            name, state_abbr = result.current_location.split(" - ")
            state_abbr = re.sub("[^a-z ]", "", state_abbr.lower())
            state = STATES_NORMALIZED.get(state_abbr)
            if state:
                result.facilities = Facility.objects.fuzzy_lookup(
                        term=name,
                        state=state,
                        administrator__name="California")

        results.append(result)

    return {'state': 'California', 'results': results, 'errors': errors, 'url': url}
