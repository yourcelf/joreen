# -*- coding: utf-8 -*-
import json

from stateparsers.states import BaseStateSearch


class Search(BaseStateSearch):
    url = "http://www.bop.gov/PublicInfo/execute/inmateloc"
    administrator_name = "Federal Bureau of Prisons"
    minimum_search_terms = [["last_name", "first_name"], ["number"]]

    def crawl(self, **kwargs):
        from facilities.models import Facility

        searches = []
        if kwargs.get("number"):
            for numtype in ("IRN", "DCDC", "FBI", "INS"):
                searches.append(
                    {"inmateNum": kwargs["number"], "inmateNumType": numtype}
                )
        else:
            searches.append(
                {
                    "nameFirst": kwargs.get("first_name"),
                    "nameLast": kwargs.get("last_name"),
                }
            )

        for i, search in enumerate(searches):
            search["todo"] = "query"
            search["output"] = "json"
            res = self.session.get(self.url, params=search)
            if res.status_code != 200:
                self.errors.append(res.content)
                break

            data = json.loads(res.content.decode("utf-8"))
            if "InmateLocator" not in data:
                self.errors.append(res.content)
                continue
            for entry in data["InmateLocator"]:
                if entry["releaseCode"] == "R":
                    status = self.STATUS_RELEASED
                    facilities = Facility.objects.none()
                elif entry["faclCode"] == "":
                    status = self.STATUS_UNKNOWN
                    facilities = Facility.objects.none()
                else:
                    status = self.STATUS_INCARCERATED
                    facilities = Facility.objects.filter(
                        administrator__name="Federal Bureau of Prisons",
                        code=entry["faclCode"],
                    )

                facl_url = entry.get("faclUrl", "")
                if facl_url:
                    facl_url = "http://www.bop.gov" + facl_url

                self.add_result(
                    name=u"{} {}".format(entry.pop("nameFirst"), entry.pop("nameLast")),
                    search_terms=search,
                    raw_facility_name=entry.get("faclCode", ""),
                    facility_url=facl_url,
                    facilities=facilities,
                    status=status,
                    numbers={entry.pop("inmateNumType"): entry.pop("inmateNum")},
                    result_url=None,
                    extra=entry,
                )
