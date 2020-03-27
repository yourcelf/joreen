import re
import requests
import lxml.html

from stateparsers.states import BaseStateSearch
from stateparsers.request_caching import ThrottleSession

_session = ThrottleSession()

class Search(BaseStateSearch):
    administrator_name = "New York"
    minimum_search_terms = [["last_name"], ["number"]]
    url = "http://nysdoccslookup.doccs.ny.gov"
    post_url = "http://nysdoccslookup.doccs.ny.gov/GCA00P00/WIQ1/WINQ000"

    # Session without caching so we get the unique DFH_STATE_TOKEN each time.
    session_nocache = _session

    def get_facilities_and_status(self, facility_name, raw_status):
        from facilities.models import Facility
        if raw_status == "IN CUSTODY":
            status = self.STATUS_INCARCERATED
            facilities = Facility.objects.find_by_name("New York", facility_name)
        elif raw_status in ("RELEASED", "DISCHARGED", "TEMP RELEASE"):
            status = self.STATUS_RELEASED
            facilities = Facility.objects.none()
        else:
            status = self.STATUS_UNKNOWN
            facilities = Facility.objects.none()
        return status, facilities

    def crawl(self, **kwargs):
        from facilities.models import Facility

        res = self.session_nocache.get(self.url)
        root = lxml.html.fromstring(res.text)
        dfh_state_token = root.xpath("//input[@name='DFH_STATE_TOKEN']/@value")[0]

        params = {
            "M00_LAST_NAMEI": kwargs.get("last_name", ""),
            "M00_FIRST_NAMEI": kwargs.get("first_name", ""),
        }

        post_data = {
            "K01": "WINQ000",
            "DFH_STATE_TOKEN": dfh_state_token, 
            "DFH_MAP_STATE_TOKEN": "",
            "M00_MID_NAMEI": "",
            "M00_NAME_SUFXI": "",
            "M00_DOBCCYYI": "",
            "M00_DIN_FLD1I": "",
            "M00_DIN_FLD2I": "",
            "M00_DIN_FLD3I": "",
            "M00_NYSID_FLD1I": "",
            "M00_NYSID_FLD2I": "",
        }

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
                    self.errors.append("Unrecognized number format")
                    return

            # Numbers must be exact, and take us directly to a single result page.
            post_data.update(params)
            res = self.session.post(self.post_url, post_data)

            if "The inmate you have chosen has multiple commitments to NYS DOCCS" in res.text:
                root = lxml.html.fromstring(res.text)
                post_data = {
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
                url = self.url + "/GCA00P00/WIQ2/WINQ120"

                # POST again to retrieve detail information from one commitment.
                res = self.session.post(url, post_data)

            if "Identifying and Location Information" in res.text:
                root = lxml.html.fromstring(res.text)
                facility_name = "".join(root.xpath("//td[@headers='t1g']/text()")).strip()
                raw_status = "".join(root.xpath("//td[@headers='t1f']//text()")).strip()
                status, facilities = self.get_facilities_and_status(facility_name, raw_status)
                name = "".join(root.xpath("//td[@headers='t1b']/text()")).strip()
                numbers = {
                    "din": "".join(root.xpath("//td[@headers='t1a']/text()")).strip()
                }

                self.add_result(
                    name=name,
                    numbers=numbers,
                    search_terms=params,
                    status=status,
                    raw_facility_name=facility_name,
                    facilities=facilities,
                    # extra
                    extra=dict(
                        sex="".join(root.xpath("//td[@headers='t1c']/text()")),
                        date_of_birth="".join(root.xpath("//td[@headers='t1d']/text()")),
                        race="".join(root.xpath("//td[@headers='t1e']/text()")),
                        status=status,
                        date_received_original="".join(root.xpath("//td[@headers='t1h']/text()")),
                        date_received_current="".join(root.xpath("//td[@headers='t1i']/text()")),
                        admission_type="".join(root.xpath("//td[@headers='t1j']/text()")),
                        county_of_commitment="".join(root.xpath("//td[@headers='t1k']/text()")),
                        latest_release_date_if_released="".join(root.xpath("//td[@headers='t1l']/text()")),
                    )
                )
            else:
                self.errors.append("Couldn't parse information by that number.")
        else:
            # Names take us to a search results page.
            post_data.update(params)
            res = self.session.post(self.post_url, post_data)
            root = lxml.html.fromstring(res.text)
            for row in root.xpath("//table[@id='dinlist']//tr"):
                tds = row.xpath('.//td')
                if len(tds) != 7:
                    continue

                name = "".join(row.xpath(".//td[@headers='name']//text()")).strip()
                if not name:
                    continue

                facility_name = "".join(row.xpath(".//td[@headers='fac']//text()")).strip()
                raw_status = "".join(row.xpath(".//td[@headers='stat']//text()")).strip()
                status, facilities = self.get_facilities_and_status(facility_name, raw_status)

                self.add_result(
                    name=name,
                    numbers={"din": "".join(row.xpath(".//td[@headers='din']//input[@type='submit']/@value")).strip()},
                    search_terms=params,
                    raw_facility_name=facility_name,
                    status=status,
                    facilities=facilities,
                    result_url = res.url,

                    # extra
                    extra=dict(
                        sex="".join(row.xpath(".//td[@headers='sex']//text()")).strip(),
                        date_of_birth="".join(row.xpath(".//td[@headers='dob']//text()")).strip(),
                        status="".join(row.xpath(".//td[@headers='stat']//text()")).strip(),
                        race="".join(row.xpath(".//td[@headers='race']//text()")).strip(),
                    )
                )
