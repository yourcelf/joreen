import re
import lxml.html

from stateparsers.states import BaseStateSearch
from stateparsers.request_caching import ThrottleSession
_session = ThrottleSession()

class Search(BaseStateSearch):
    administrator_name = "California"
    minimum_search_terms = [["last_name"], ["number"]]
    url = "http://inmatelocator.cdcr.ca.gov/search.aspx"
    auth_url = "http://inmatelocator.cdcr.ca.gov/default.aspx"

    # California doesn't cache well with its terms interstitial.  Attempts
    # to work around have thus been unsuccessful, so just disable cache for
    # this state.
    session = _session

    def crawl(self, **kwargs):
        from facilities.models import Facility

        # Get the auth cookie
        res = self.session.get(self.auth_url)
        root = lxml.html.fromstring(res.text)
        data = {
            "__EVENTVALIDATION": "".join(root.xpath('//input[@id="__EVENTVALIDATION"]/@value')),
            '__VIEWSTATE': ''.join(root.xpath('//input[@id="__VIEWSTATE"]/@value')),
            '__EVENTTARGET': "",
            '__EVENTARGUMENT': "",
            'text': ''.join(root.xpath('//textarea[@name="text"]/text()')),
            "ctl00$LocatorPublicPageContent$btnAccept": "Agree",
        }
        self.session.post("http://inmatelocator.cdcr.ca.gov/default.aspx", data)

        # Now do the search
        res = self.session.get(self.url)
        root = lxml.html.fromstring(res.text)
        params = {
            "ctl00$LocatorPublicPageContent$txtLastName": kwargs.get("last_name", ""),
            "ctl00$LocatorPublicPageContent$txtFirstName": kwargs.get("first_name", ""),
            "ctl00$LocatorPublicPageContent$txtCDCNumber": kwargs.get("number", ""),
        }
        query = {
            "ctl00$LocatorPublicPageContent$txtMiddleName": "",
            "ctl00$LocatorPublicPageContent$btnSearch": "Search",
            "__LASTFOCUS": "",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__EVENTVALIDATION": ''.join(root.xpath('//input[@id="__EVENTVALIDATION"]/@value')),
            "__VIEWSTATE": ''.join(root.xpath('//input[@id="__VIEWSTATE"]/@value')),

        }
        query.update(params)
        res = self.session.post(self.url, query)

        # Now parse the results.
        root = lxml.html.fromstring(res.text)
        rows = root.xpath('//table[@id="ctl00_LocatorPublicPageContent_gvGridView"]//tr')
        for row in rows:
            if len(row.xpath('./td')) == 0:
                continue
            name = "".join(row.xpath('(./td)[1]/text()'))
            if not name:
                text = u''.join(row.xpath('//text()')).strip()
                if "Next Page" in text or "Previous Page" in text or re.search("Page \d+ of \d+", text):
                    continue
                else:
                    self.errors.append(text)
                    continue

            current_location = ''.join(row.xpath('(./td)[5]/a/text()')).strip()
            current_location_url = ''.join(row.xpath('(./td)[5]/a/@href')).strip()

            result = self.add_result(
                name=name,
                numbers={"CDCR": "".join(row.xpath('(./td)[2]/text()'))},
                search_terms=params,
                status=self.STATUS_INCARCERATED,
                raw_facility_name=current_location,
                facility_url=current_location_url,
                facilities = Facility.objects.find_by_name("California", current_location),
                extra=dict(
                    age="".join(row.xpath('(./td)[3]/text()')),
                    admission_date=''.join(row.xpath('(./td)[4]/text()')),
                    map_url=''.join(row.xpath('(./td)[6]/a/@href')),
                )
            )
