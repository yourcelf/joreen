import re
import requests
import lxml.html

from stateparsers.states import LookupResult, normalize_name
 
texas_unit_type_re = re.compile(" (Unit|Complex|Transfer Facility|Prison|State Jail|Medical Facility|Geriatric Facility|Correctional (Center|Facility)|Treatment( Facility)?)$", re.I)

facility_name_overrides = {
    'carol young complex': 'Carole S. Young Medical Facility',
    'diboll priv': 'Diboll Correctional Center',
    'east texas treatment facility': 'East Texas Multi-Use Facility',
    'hospital galv': 'Hospital Galveston',
    'jester i': 'Beauford H. Jester I Unit',
    'jester ii': 'Beauford H. Jester II Unit',
    'jester iii': 'Beauford H. Jester III Unit',
    'jester iv': 'Beauford H. Jester IV Unit',
    'lockhart work fac': 'Lockhart Correctional Facility',
    'pack i': 'Wallace Pack Unit',
    'ramsey i': 'W. F. Ramsey Unit',
    'west texas isf': 'West Texas Intermediate Sanction Facility',
    'west texas hosp': 'West Texas Intermediate Sanction Facility',
}

def normalize_texas_name(name):
    name = normalize_name(name)
    if name in facility_name_overrides:
        return normalize_name(facility_name_overrides[name])
    return name 

def search(**kwargs):
    url = "http://offender.tdcj.state.tx.us/OffenderSearch/search.action"

    # Fix number formatting
    number = kwargs.get('number', '')
    if number:
        number_types = ("tdcj", "sid")
        number = re.sub('[^0-9]', '', number)
        number = "0" * (8 - len(number)) + number
    else:
        number_types = ("sid")

    results = []
    errors = []

    for number_type in number_types:
        params = {
            "page": "index",
            "lastName": kwargs.get('last_name', ''),
            "firstName": kwargs.get('first_name', ''),
            "gender": "ALL",
            "race": "ALL",
            "btnSearch": "Search",
        }
        params[number_type] = number
        res = requests.post(url, params)

        root = lxml.html.fromstring(res.text)
        rows = root.xpath('//table[@class="ws"]//tr')
        for row in rows:
            name = "".join(row.xpath('./td[1]/a/text()'))
            if not name:
                continue

            result_url = "http://offender.tdcj.state.tx.us" + "".join(row.xpath('./td[1]/a/@href')) 
            numbers = {"tdcj_number": "".join(row.xpath('./td[2]/text()'))}
            match = re.search("sid=([-0-9a-zA-Z]+)", result_url)
            if match:
                numbers['sid_number'] = match.group(1)

            unit_of_assignment = "".join(row.xpath('./td[6]/text()'))
            if unit_of_assignment:
                status = LookupResult.STATUS_INCARCERATED
                facilities = Facility.objects.fuzzy_lookup(
                    term=normalize_texas_name(unit_of_assignment),
                    administrator__name="Texas")
            else:
                status = LookupResult.STATUS_UNKNOWN
                facilities = None

            result = LookupResult(
                name=name,
                numbers=numbers,
                status=status,
                facilities=facilities,
                search_url=url,
                result_url=result_url,
                extra={
                    'unit_of_assignment': unit_of_assingment,
                    'race': "".join(row.xpath('./td[3]/text()')),
                    'gender': "".join(row.xpath('./td[4]/text()')),
                    'projected_release_date': "".join(row.xpath('./td[5]/text()')),
                    'date_of_birth': "".join(row.xpath('./td[7]/text()')),
                }
            )
            results.append(result)

        if results:
            break
    return {'state': 'Texas', 'results': results, 'errors': list(errors), 'url': url}
