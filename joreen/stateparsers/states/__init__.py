# -*- coding: utf-8 -*-
import re

from stateparsers.request_caching import get_caching_session
from fuzzywuzzy import fuzz


class LookupStatus(object):
    STATUS_INCARCERATED = "Incarcerated"
    STATUS_RELEASED = "Released"
    STATUS_UNKNOWN = "Unknown"


class LookupResult(LookupStatus):
    kwargs = [
        "name",
        "numbers",
        "status",
        "facilities",
        "raw_facility_name",
        "facility_url",
        "search_url",
        "result_url",
        "search_terms",
        "administrator_name",
        "extra",
    ]

    def __init__(self, **kwargs):
        for kwarg in self.kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def to_dict(self):
        dct = {}
        for key in self.kwargs:
            dct[key] = getattr(self, key)
        dct["facilities"] = list(map(lambda f: f.to_result_dict(), dct["facilities"]))
        return dct


_session = get_caching_session()


class BaseStateSearch(LookupStatus):

    # Source URL to report to users
    url = ""
    # Name of the FacilityAdminsitrator we're searching, e.g. 'California'
    administrator_name = ""
    # List of lists of minimum allowed search terms
    minimum_search_terms = [["last_name"], ["first_name"], ["number"]]

    # All possible search terms.
    _search_terms = set(["last_name", "first_name", "number"])

    session = _session

    def search(self, **kwargs):
        # Import here rather than top-level
        # https://github.com/django/django-localflavor/issues/203
        from stateparsers.models import FacilityNameResult

        self.check_minimum_terms(kwargs)
        self.errors = []
        self.results = []
        self.crawl(**kwargs)
        for result in self.results:
            if result.raw_facility_name:
                FacilityNameResult.objects.log_name(
                    self.administrator_name,
                    result.raw_facility_name,
                    result.facility_url,
                )
        return {"results": self.results, "errors": self.errors}

    def add_result(self, **kwargs):
        # Import here rather than top-level
        # https://github.com/django/django-localflavor/issues/203
        from stateparsers.models import Facility

        opts = {
            "administrator_name": self.administrator_name,
            "status": self.STATUS_UNKNOWN,
            "raw_facility_name": "",
            "facility_url": "",
            "facilities": Facility.objects.none(),
            "search_url": self.url,
            "result_url": None,
            "extra": None,
        }
        opts.update(kwargs)
        result = LookupResult(**opts)
        self.results.append(result)
        return result

    @classmethod
    def get_state(cls, abbr):
        # Import here rather than top-level
        # https://github.com/django/django-localflavor/issues/203
        from localflavor.us.us_states import STATES_NORMALIZED

        abbr = re.sub("[^a-z ]", "", abbr.lower())
        return STATES_NORMALIZED.get(abbr)

    def crawl(self, **kwargs):
        raise NotImplementedError

    def check_minimum_terms(self, kwargs):
        for minimum in self.minimum_search_terms:
            for term in minimum:
                if term not in kwargs or not kwargs[term]:
                    break
            else:
                return True
        found_terms = [k for k in kwargs.keys() if k in self._search_terms]
        raise MinimumTermsError(
            self.administrator_name, self.minimum_search_terms, found_terms
        )

    @classmethod
    def normalize_name(cls, name):
        # Replace all but - and a-z with emptystring.
        name = re.sub("[^-a-z ]", "", name.lower()).strip()
        # Replace - with single space " "
        name = re.sub("-", " ", name)
        # Remove multiple spaces
        name = re.sub(r"\s+", " ", name)
        return name


class MinimumTermsError(Exception):
    def __init__(self, state, minimum_terms, found_terms):
        self.state = state
        self.minimum_terms = minimum_terms
        super(MinimumTermsError, self).__init__(
            "{} requires one of {}.  {} given.".format(
                state, minimum_terms, found_terms
            )
        )


def fuzzy_match_address(address, choices):
    scores = []
    for choice in choices:
        score = []
        # Zip handling
        if address.get("state") is not None and address.get("state") != choice.get(
            "state"
        ):
            continue
        z1 = address.get("zip")
        z2 = choice.get("zip")
        if z1 and z2:
            score.append(fuzz.partial_ratio(z1, z2))
        # City, org, address
        for key in ["city", "address1", "organization"]:
            v1 = address.get(key)
            v2 = choice.get(key)
            if v1 is not None and v2 is not None:
                v1 = re.sub("[^a-z0-9 ]", "", v1.lower())
                v2 = re.sub("[^a-z0-9 ]", "", v2.lower())
                score.append(fuzz.ratio(v1, v2))
        if score:
            scores.append((sum(score) / float(len(score)), choice))

    if len(scores) == 0:
        return 0, None

    scores.sort()
    return scores[-1][0], scores[-1][1]
