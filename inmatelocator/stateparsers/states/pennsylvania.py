import re
import requests
import json

from stateparsers.states import BaseStateSearch

class Search(BaseStateSearch):
    administrator_name = "Pennsylvania"
    minimum_search_terms = [["last_name"], ["first_name"], ["number"]]
    url = "https://captorapi.cor.pa.gov/InmLocAPI/api/v1/InmateLocator/SearchResults"

    def crawl(self, **kwargs):
        from facilities.models import Facility

        params = {
            "id": kwargs.get('number', ""),
            'lastName': kwargs.get('last_name', ""),
            'firstName': kwargs.get('first_name', ""),
        }

        post_data = {
            "middleName": "",
            "countylistkey": "---",
            "citizenlistkey": "---",
            "racelistkey": "---",
            "sexlistkey": "---",
            "locationlistkey": "---",
            "sortBy": "1"
        }
        post_data.update(params)

        res = self.session.post(self.url, json=post_data)
        if res.status_code != 200:
            self.errors.append(res.content)
            return

        results = json.loads(res.text)

        for result in results.get("inmates", []):
            name_part_keys = ["inm_firstname", "inm_middlename", "inm_lastname", "inm_suffix"]
            name_parts = [result.get(key) for key in name_part_keys]
            name = " ".join([a for a in name_parts if a])
            raw_facility_name = result.get('fac_name')
            self.add_result(
                name=name,
                numbers={"": result.get("inmate_number")},
                search_terms=params,
                raw_facility_name=raw_facility_name,
                status=self.STATUS_INCARCERATED,
                facilities=Facility.objects.find_by_name("Pennsylvania", raw_facility_name),
                extra=dict(
                    race=result.get('race'),
                    date_of_birth=result.get('dob'),
                    cnty_name=result.get('cnty_name')
                )
            )
