# -*- coding: utf-8 -*-
from collections import defaultdict
from urllib.parse import urlencode
import re
import requests
import lxml.html

from stateparsers.states import BaseStateSearch

# Load facility data.

class Search(BaseStateSearch):
    administrator_name = "Florida"
    minimum_search_terms = [["first_name"], ["last_name"], ["number"]]
    url = "http://www.dc.state.fl.us/OffenderSearch/list.aspx"
    detail_url = 'http://www.dc.state.fl.us/offenderSearch/detail.aspx'

    def crawl(self, **kwargs):
        from facilities.models import Facility

        # Florida has a wonky system where you first search using a form, which
        # then generates a link to one of 4 different search pages that segment
        # the results by incarceration status.  Bypass the initial form and go
        # straight to the list page.
        #
        # Once we get to the list page, we still need to visit each detail link
        # separately in order to get facility info.

        result_types = {
            # General inmate population
            'AI': self.STATUS_INCARCERATED,
            # Released
            'IR': self.STATUS_RELEASED,
            # Treat "supervised" as "released" for address purposes
            'AO': self.STATUS_RELEASED, # Supervised
            # Absconder / Fugitive. Ignore for now.
            #'AB': self.STATUS_INCARCERATED, # Absconder/Fugitive list
        }
        params = {
            'dcnumber': kwargs.get('number', ''),
            'LastName': kwargs.get('last_name', ''),
            'FirstName': kwargs.get('first_name', ''),
        }

        results_by_type_search = defaultdict(list)
        for type_search, status in result_types.items():
            query = {}
            query.update(params)
            query.update({
                'Page': 'List',
                'TypeSearch': type_search,
                'DataAction': 'Filter',
                'SearchAliases': '0',
                'OffenseCategory': '',
                'photosonly': '0',
                'nophotos': '1',
                'matches': '20',
            })

            res = self.session.get('%s?%s' % (self.url, urlencode(query))) 
            root = lxml.html.fromstring(res.text)
            rows = root.xpath('//table[@id="ctl00_ContentPlaceHolder1_grdList"]//tr')
            for row in rows:
                tds = row.xpath('./td')
                if len(tds) != 8:
                    continue
                dc_number = ''.join(tds[2].xpath('.//text()')).strip()
                name = ''.join(tds[1].xpath('.//text()')).strip()
                results_by_type_search[type_search].append({
                    'number': dc_number,
                    'name': name
                })

        for type_search, results in results_by_type_search.items():
            for result in results:
                status = result_types[type_search]

                detail_url = '{}?{}'.format(
                    self.detail_url,
                    urlencode({
                        'Page': 'Detail',
                        'DCNumber': result['number'],
                        'TypeSearch': type_search
                    })
                )

                if status == self.STATUS_RELEASED:
                    facilities = Facility.objects.none()
                    raw_facility = ''
                else:
                    res = self.session.get(detail_url)
                    root = lxml.html.fromstring(res.text)
                    detail_rows = root.xpath(
                        '//table[@class="offenderDetails"]//tr'
                    )
                    raw_facility = ''
                    for row in detail_rows:
                        tds = row.xpath('./td')
                        field = ''.join(tds[0].xpath('.//text()')).strip()
                        if 'Current Facility' in field:
                            raw_facility = ''.join(tds[1].xpath('./text()')).strip()
                    if raw_facility:
                        facilities = Facility.objects.find_by_name(
                            "Florida", raw_facility
                        )
                    else:
                        facilities = Facility.objects.none()

                self.add_result(
                    search_terms=params,
                    name=result['name'],
                    numbers={"dc_number": result['number']},
                    status=status,
                    search_url=self.url,
                    result_url=detail_url,
                    facilities=facilities,
                    raw_facility=raw_facility,
                )
