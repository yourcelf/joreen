import re
import requests
import lxml.html

from stateparsers.states import LookupResult, normalize_name
from facilities.models import Facility

def normalize_facility_name(term):
    return normalize_name(term)

def search(**kwargs):
    base = "http://nysdoccslookup.doccs.ny.gov"
    search = "http://nysdoccslookup.doccs.ny.gov/GCA00P00/WIQ1/WINQ000"

    res = requests.get(base)
    root = lxml.html.fromstring(res.text)
    dfh_state_token = root.xpath("//input[@name='DFH_STATE_TOKEN']/@value")[0]

    params = {
        "K01": "WINQ000",
        "DFH_STATE_TOKEN": dfh_state_token, 
        "DFH_MAP_STATE_TOKEN": "",
        "M00_LAST_NAMEI": kwargs.get("last_name", ""),
        "M00_FIRST_NAMEI": kwargs.get('first_name', ''),
        "M00_MID_NAMEI": "",
        "M00_NAME_SUFXI": "",
        "M00_DOBCCYYI": "",
        "M00_DIN_FLD1I": "",
        "M00_DIN_FLD2I": "",
        "M00_DIN_FLD3I": "",
        "M00_NYSID_FLD1I": "",
        "M00_NYSID_FLD2I": "",
    }

    errors = []
    results = []

    if kwargs.get('number'):
        number = kwargs['number']
        match = re.match("(\d\d)-?(\w)-?(\d\d\d\d)", number)
        if match:
            params["M00_DIN_FLD1I"] = match.group(1)
            params["M00_DIN_FLD2I"] = match.group(2)
            params["M00_DIN_FLD3I"] = match.group(3)
        else:
            match = re.match("(\w{8})-?(\w)", number)
            if match:
                params["M00_NYSID_FLD1I"] = match.group(1)
                params["M00_NYSID_FLD2I"] = match.group(2)
            else:
                errors.append("Unrecognized number format")

        # Numbers must be exact, and take us directly to a single result page.
        res = requests.post(search, params)
        root = lxml.html.fromstring(res.text)
        if "The inmate you have chosen has multiple commitments to NYS DOCCS" in res.text:
            params = {
                "M12_SEL_DINI": root.xpath("//input[@name='M12_SEL_DINI']/@value")[0],
                "K01": root.xpath("//input[@name='K01']/@value")[0],
                "K02": root.xpath("//input[@name='K02']/@value")[0],
                "K03": root.xpath("//input[@name='K03']/@value")[0],
                "K04": root.xpath("//input[@name='K03']/@value")[0],
                "K05": root.xpath("//input[@name='K03']/@value")[0],
                "K06": root.xpath("//input[@name='K03']/@value")[0],
                "DFH_STATE_TOKEN": root.xpath("//input[@name='DFH_STATE_TOKEN']/@value")[0],
                "DFH_MAP_STATE_TOKEN": root.xpath("//input[@name='DFH_MAP_STATE_TOKEN']/@value")[0],
                "din1": root.xpath("//input[@name='din1']/@value")[0],
            }
            url = base + "/GCA00P00/WIQ2/WINQ120"
            res = requests.post(url, params)
        if "Identifying and Location Information" in res.text:

            facility_name = "".join(root.xpath("//td[@headers='t1g']/text()")).strip()
            facilities = Facility.objects.fuzzy_lookup(
                    term=normalize_facility_name(facility_name),
                    administrator__name="New York")

            result = LookupResult(
                name="".join(root.xpath("//td[@headers='t1b']/text()")),
                numbers={"din": "".join(root.xpath("//td[@headers='t1a']/text()"))},
                status=LookupResult.STATUS_INCARCERATED,
                facilities=facilities,
                search_url=base,
                result_url=None,

                # extra
                extra=dict(
                    sex="".join(root.xpath("//td[@headers='t1c']/text()")),
                    date_of_birth="".join(root.xpath("//td[@headers='t1d']/text()")),
                    race="".join(root.xpath("//td[@headers='t1e']/text()")),
                    custody_status="".join(root.xpath("//td[@headers='t1f']/text()")),
                    date_received_original="".join(root.xpath("//td[@headers='t1h']/text()")),
                    date_received_current="".join(root.xpath("//td[@headers='t1i']/text()")),
                    admission_type="".join(root.xpath("//td[@headers='t1j']/text()")),
                    county_of_commitment="".join(root.xpath("//td[@headers='t1k']/text()")),
                    latest_release_date_if_released="".join(root.xpath("//td[@headers='t1l']/text()")),
                )
            )
            results.apppend(result)
        else:
            errors.append("Couldn't parse information by that number.")
    else:
        # Names take us to a search results page.
        res = requests.post(search, params)
        root = lxml.html.fromstring(res.text)
        for row in root.xpath("//table[@id='dinlist']//tr"):
            tds = row.xpath('.//td')
            if len(tds) != 7:
                continue

            name = "".join(row.xpath(".//td[@headers='name']//text()")).strip()
            if not name:
                continue

            facility_name = "".join(row.xpath(".//td[@headers='fac']//text()")).strip()
            facilities = Facility.objects.filter(
               term=normalize_facility_name(facility_name),
               administrator__name="New York"
            )

            result = LookupResult(
                name=name,
                numbers={"din": "".join(row.xpath(".//td[@headers='din']//input[@type='submit']/@value")).strip()},
                status=LookupResult.STATUS_INCARCERATED,
                search_url=base,
                result_url=None,
                facilities=facilities,

                # extra
                extra=dict(
                    sex="".join(row.xpath(".//td[@headers='sex']//text()")).strip(),
                    date_of_birth="".join(row.xpath(".//td[@headers='dob']//text()")).strip(),
                    status="".join(row.xpath(".//td[@headers='stat']//text()")).strip(),
                    race="".join(row.xpath(".//td[@headers='race']//text()")).strip(),
                )
            )
            results.append(result)
    return {'state': 'Florida', 'results': results, 'errors': errors, 'url': base}
