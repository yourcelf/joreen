import re
import requests
import lxml.html

from stateparsers.states import BaseStateSearch
from facilities.models import Facility

class Search(BaseStateSearch):
    administrator_name = "Pennsylvania"
    minimum_search_terms = [["last_name"], ["first_name"], ["number"]]
    url = "http://inmatelocator.cor.state.pa.us/inmatelocatorweb/"

    def crawl(self, **kwargs):

        # Get the session cookie.
        res = self.session.get(self.url)
        root = lxml.html.fromstring(res.text)

        params = {
           'txtLstNm': kwargs.get('last_name'),
           'txtFrstNm': kwargs.get('first_name'),
           'txtInmNo': kwargs.get('number'),
       }

        data = {
            'txtMidNm': '',
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
        data.update(params)

        for key in ("__EVENTVALIDATION", "__VIEWSTATE", "__VIEWSTATEGENERATOR",
                    "__EVENTTARGET", "__EVENTARGUMENT"):
            data[key] = "".join(root.xpath('//input[@id="{}"]/@value'.format(key))) 

        res = self.session.post(self.url, data)
        root = lxml.html.fromstring(res.text)
        rows = root.xpath("//tr[@class='clstdfield']")
        results = []
        errors = []
        for row in rows:
            texts = [' '.join(td.xpath('.//text()')).strip() for td in row.xpath('./td')]
            texts = [re.sub('\s+', ' ', part) for part in texts]
            number, first_name, middle_name, last_name, suffix, race, dob, current_location, committing_county = texts
            name = " ".join((n for n in (first_name, middle_name, last_name) if n))
            if suffix:
                name = "{}, {}".format(name, suffix)

            # filter also-known-as results.
            skip = False
            for name_part in ('first_name', 'last_name'):
                if name_part in kwargs:
                    if kwargs[name_part].lower() not in name.lower():
                        skip = True
                        break
            if skip:
                continue


            self.add_result(
                name=name,
                numbers={"": number},
                search_terms=params,
                raw_facility_name=current_location,
                status=self.STATUS_INCARCERATED,
                facilities=Facility.objects.find_by_name("Pennsylvania", current_location),
                extra=dict(
                    race=race,
                    date_of_birth=dob,
                    committing_county=committing_county
                )
            )




