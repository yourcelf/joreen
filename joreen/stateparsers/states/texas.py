import traceback
import re
import requests
import lxml.html

from stateparsers.states import BaseStateSearch

texas_unit_type_re = re.compile(
    " (Unit|Complex|Transfer Facility|Prison|State Jail|Medical Facility|Geriatric Facility|Correctional (Center|Facility)|Treatment( Facility)?)$",
    re.I,
)

facility_name_overrides = {
    "carol young complex": "Carole S. Young Medical Facility",
    "diboll priv": "Diboll Correctional Center",
    "east texas treatment facility": "East Texas Multi-Use Facility",
    "hospital galv": "Hospital Galveston",
    "jester i": "Beauford H. Jester I Unit",
    "jester ii": "Beauford H. Jester II Unit",
    "jester iii": "Beauford H. Jester III Unit",
    "jester iv": "Beauford H. Jester IV Unit",
    "lockhart work fac": "Lockhart Correctional Facility",
    "pack i": "Wallace Pack Unit",
    "ramsey i": "W. F. Ramsey Unit",
    "west texas isf": "West Texas Intermediate Sanction Facility",
    "west texas hosp": "West Texas Intermediate Sanction Facility",
    "alfred hughes": "Alfred D. Hughes Unit",
    "joe f gurney": "Joe F. Gurney Transfer Facility",
    "travis jail": "Travis County State Jail",
    "bill clements": "William P. Clements Unit",
    "mac stringfellow": 'A.M. "Mac" Stringfellow Unit',
}

#   'texas': [["last_name", "first_name"], ["number"]],


class Search(BaseStateSearch):
    administrator_name = "Texas"
    minimum_search_terms = [["last_name", "first_name"], ["number"]]
    base_url = "https://offender.tdcj.texas.gov"
    url = "%s/OffenderSearch/search.action" % base_url

    @classmethod
    def normalize_name(cls, name):
        norm = super(Search, cls).normalize_name(name)
        if norm in facility_name_overrides:
            return facility_name_overrides[norm]
        return norm

    def crawl(self, **kwargs):
        from facilities.models import Facility

        # Fix number formatting
        number = kwargs.get("number", "")
        if number:
            number_types = ("tdcj", "sid")
            number = re.sub("[^0-9]", "", number)
            number = "0" * (8 - len(number)) + number
        else:
            number_types = ("sid",)

        for number_type in number_types:
            params = {
                "page": "index",
                "lastName": kwargs.get("last_name", ""),
                "firstName": kwargs.get("first_name", ""),
                "gender": "ALL",
                "race": "ALL",
                "btnSearch": "Search",
                "tdcj": "",
                "sid": "",
            }
            params[number_type] = number
            try:
                res = self.session.post(self.url, params)
            except Exception as e:
                self.errors.append(traceback.format_exc())
                continue

            root = lxml.html.fromstring(res.text)
            rows = root.xpath('//table[@class="tdcj_table"]//tr')
            for row in rows:
                name = "".join(row.xpath("./td[1]/a/text()"))
                if not name:
                    continue

                result_url = self.base_url + "".join(row.xpath("./td[1]/a/@href"))
                numbers = {"tdcj_number": "".join(row.xpath("./td[2]/text()"))}
                match = re.search("sid=([-0-9a-zA-Z]+)", result_url)
                if match:
                    numbers["sid_number"] = match.group(1)

                unit_of_assignment = "".join(row.xpath("./td[6]/text()"))
                if unit_of_assignment == "TEMP RELEASE":
                    status = self.STATUS_RELEASED
                    facilities = Facility.objects.none()
                elif unit_of_assignment:
                    status = self.STATUS_INCARCERATED
                    facilities = Facility.objects.find_by_name(
                        "Texas", unit_of_assignment
                    )
                else:
                    status = self.STATUS_UNKNOWN
                    facilities = Facility.objects.none()

                self.add_result(
                    name=name,
                    numbers=numbers,
                    search_terms=params,
                    raw_facility_name=unit_of_assignment,
                    result_url=result_url,
                    facilities=facilities,
                    extra={
                        "unit_of_assignment": unit_of_assignment,
                        "race": "".join(row.xpath("./td[3]/text()")),
                        "gender": "".join(row.xpath("./td[4]/text()")),
                        "projected_release_date": "".join(row.xpath("./td[5]/text()")),
                        "date_of_birth": "".join(row.xpath("./td[7]/text()")),
                    },
                )

            if self.results:
                break
