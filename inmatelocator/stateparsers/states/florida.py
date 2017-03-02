# -*- coding: utf-8 -*-
import re
import requests
import lxml.html

from stateparsers.states import BaseStateSearch

# Load facility data.

class Search(BaseStateSearch):
    administrator_name = "Florida"
    minimum_search_terms = [["first_name"], ["last_name"], ["number"]]
    url = "http://www.dc.state.fl.us/ActiveInmates/search.asp"
    post_url = "http://www.dc.state.fl.us/ActiveInmates/List.asp?DataAction=Filter"

    def crawl(self, **kwargs):
        from facilities.models import Facility

        res = self.session.get(self.url)
        root = lxml.html.fromstring(res.text)
        sessionId = root.xpath("//input[@name='SessionID']/@value")[0]

        params = {
            "lastname": kwargs.get('last_name', ''),
            "firstname": kwargs.get('first_name', ''),
            "dcnumber": kwargs.get('number', ''), 
        }
        post_data = {
            "SessionID": sessionId,
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
        }
        post_data.update(params)

        res = self.session.post(self.post_url, post_data)

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

            if current_facility == "OUT OF DEPT. CUSTODY BY COURT ORDER":
                status = self.STATUS_RELEASED
                facilities = Facility.objects.none()
            else:
                status = self.STATUS_INCARCERATED
                facilities = Facility.objects.find_by_name(
                    "Florida", current_facility
                )

            self.add_result(
                name=name,
                search_terms=params,
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
