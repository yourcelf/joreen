# -*- coding: utf-8 -*-
import re
import requests
import lxml.html

from stateparsers.states import BaseStateSearch
from facilities.models import Facility

# Load facility data.

# Mapping from things we get from the search API to normalized names from the
# directory.
facility_name_overrides = {
  'apalachee east unit': 'Apalachee Correctional Institution East',
  'apalachee west unit': 'Apalachee Correctional Institution West',
  'jackson work camp': 'Jackson Correctional Institution',
  'baker re entry centr': 'Baker Correctional Institution',
  'blackwater cf': 'Blackwater River Correctional Facility',
  'everglades re entry': 'Everglades Correctional Institution',
  'flwomens recpnctr': 'Florida Womens Reception Center',
  'okeechobee work camp': 'Okeechobee',
  'rmc main unit': 'Reception and Medical Center',
  'rmc west unit': 'Reception and Medical Center West Unit',
  'sago palm re entry c': 'Sago Palm Re-Entry Center',
  'sfrc': 'South Florida Reception Center',
  'suncoast crcfem': 'Suncoast Community Release Center',
  'union work camp': 'Union Correctional Work Camp',
  'reentry ctr of ocala': 'Re-Entry Center Of Ocala',
}

class Search(BaseStateSearch):
    administrator_name = "Florida"
    minimum_search_terms = [["first_name"], ["last_name"], ["number"]]
    url = "http://www.dc.state.fl.us/ActiveInmates/search.asp"
    post_url = "http://www.dc.state.fl.us/ActiveInmates/List.asp?DataAction=Filter"

    @classmethod
    def normalize_name(cls, name):
        norm = super(Search, cls).normalize_name(name)
        if norm in facility_name_overrides:
            return facility_name_overrides[norm]
        norm = re.sub(r'\bci(\b|$)', "correctional institution", norm)
        norm = re.sub(r'\bcf(\b|$)', "correctional facility", norm)
        return norm

    def crawl(self, **kwargs):
        res = self.session.get(self.url)
        root = lxml.html.fromstring(res.text)
        sessionId = root.xpath("//input[@name='SessionID']/@value")[0]

        res = self.session.post(self.post_url, {
                "SessionID": sessionId,
                "lastname": kwargs.get('last_name', ''),
                "firstname": kwargs.get('first_name', ''),
                "dcnumber": kwargs.get('number', ''), 
                #"searchaliases": "on", # (decreases result quality)
                "race": "ALL",
                "sex": "ALL",
                "eyecolor": "ALL",
                "haircolor": "ALL",
                "fromheightfeet": "",
                "fromheightinches": "",
                "toheightfeet": "",
                "toheightinches": "",
                "fromweight": "",
                "toweight": "",
                "fromage": "",
                "toage": "",
                "offensecategory": "ALL",
                "commitmentcounty": "ALL",
                "facility2": "ALL",
                "items": "20"
            })

        root = lxml.html.fromstring(res.text)
        rows = root.xpath('//table[@class="dcCSStableLight"]//tr')

        for row in rows:
            tds = row.xpath('./td')
            if len(tds) != 8:
                continue

            name = "".join(tds[1].xpath('.//text()')).strip()
            if not name:
                continue
            
            result_url = "".join(tds[1].xpath('.//a/@href')).strip(),
            if result_url:
                result_url = "http://www.dc.state.fl.us/ActiveInmates{}".format(result_url)
            photo = "".join(tds[0].xpath('.//img/@src')).strip()
            if photo:
                photo = "http://www.dc.state.fl.us{}".format(photo)

            current_facility = "".join(tds[6].xpath('.//text()')).strip()

            facilities = Facility.objects.find_by_name(
                "Florida", self.normalize_name(current_facility)
            )

            self.add_result(
                name=name,
                numbers={"dc_number": "".join(tds[2].xpath('.//text()')).strip()},
                status=self.STATUS_INCARCERATED,
                facilities=facilities,
                search_url=self.url,
                result_url=result_url,
                raw_facility_name=current_facility,
                # extra
                extra=dict(
                    photo=photo,
                    race="".join(tds[3].xpath('.//text()')).strip(),
                    sex="".join(tds[4].xpath('.//text()')).strip(),
                    release_date="".join(tds[5].xpath('.//text()')).strip(),
                    birth_date="".join(tds[7].xpath('.//text()')).strip(),
                )
            )
