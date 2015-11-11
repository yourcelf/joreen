from django.test import TestCase

from stateparsers import search
from stateparsers.models import FacilityNameResult

class TestState(TestCase):
    fixtures = ['facilities.json']

    def check_search(self, **terms):
        results = search(self.mod_name, **terms)
        self.assertTrue(len('results') > 0)
        self.assertEquals(results['errors'], [])
        for res in results['results']:
            self.check_result(res, **terms)

    def check_result(self, res, **kwargs):
        for name_part in ('last_name', 'first_name'):
            if name_part in kwargs:
                for part in kwargs[name_part].split():
                    self.assertTrue(part.lower() in res.name.lower(),
                        "Name mismatch: expected {}, actual {}".format(kwargs[name_part], res.name))
        if 'number' in kwargs:
            self.assertTrue(kwargs['number'] in res.numbers.values(),
                "Number mismatch: {} not found in {}".format(kwargs['number'], res.numbers))
        self.assert_enough_facilities(res)
        self.assert_logged_facility_name(res)


    def assert_enough_facilities(self, res):
        if res.status != res.STATUS_RELEASED and res.raw_facility_name:
            self.assertTrue(res.facilities.count() >= 1,
                "No facility found: {}, {}, {}, {}, {}".format(
                    res.name,
                    res.numbers.values(),
                    res.status,
                    res.raw_facility_name,
                    res.facility_url
                )
            )

    def assert_logged_facility_name(self, res):
        if res.raw_facility_name:
            self.assertEquals(FacilityNameResult.objects.filter(
                administrator__name=self.admin_name,
                name=res.raw_facility_name,
                facility_url=res.facility_url,
            ).count(), 1)


class TestCalifornia(TestState):
    admin_name = "California"
    mod_name = "CA"

    def test_search(self):
        self.check_search(last_name="johnson")
        self.check_search(number="H72354")

class TestFederal(TestState):
    admin_name = "Federal Bureau of Prisons"
    mod_name = "federal"
    def test_search(self):
        self.check_search(first_name="john", last_name="smith")
        self.check_search(number="11563-027")

class TestFlorida(TestState):
    admin_name = "Florida"
    mod_name = "FL"
    def test_search(self):
        self.check_search(first_name="john", last_name="smith")
        self.check_search(number="J48121")

class TestNewYork(TestState):
    admin_name = "New York"
    mod_name = "NY"
    def test_search(self):
        self.check_search(number="13A1038")
        self.check_search(last_name="mitch")
        self.check_search(first_name="john", last_name="smith")

class TestPennsylvania(TestState):
    admin_name = "Pennsylvania"
    mod_name = "PA"
    def test_search(self):
        self.check_search(first_name="john")
        self.check_search(number="KA3038")

class TestTexas(TestState):
    admin_name = "Texas"
    mod_name = "TX"
    def test_search(self):
        self.check_search(first_name="john", last_name="smith")
        self.check_search(number="01715697")
