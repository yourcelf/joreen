import pytest
from django.core.management import call_command

from stateparsers import search
from stateparsers.models import FacilityNameResult


@pytest.fixture
def facilities():
    call_command("loaddata", "facilities.json")


@pytest.mark.django_db
class TestState:
    def check_search(self, **terms):
        # Do each two times to make sure that the caching aparatus doesn't
        # bork.  Searches that don't support caching will hit twice, those that
        # do support caching should just return instantly.
        for i in range(2):
            results = search(self.mod_name, **terms)
            assert len(results["results"]) > 0, "0 results for {}".format(repr(terms))
            assert results["errors"] == []
            for res in results["results"]:
                self.check_result(res, **terms)

    def check_result(self, res, **kwargs):
        for name_part in ("last_name", "first_name"):
            if name_part in kwargs:
                for part in kwargs[name_part].split():
                    assert (
                        part.lower() in res.name.lower()
                    ), "Name mismatch: expected {}, actual {}".format(
                        kwargs[name_part], res.name
                    )
        if kwargs.get("number"):
            print(res)
            assert (
                kwargs["number"] in res.numbers.values()
            ), "Number mismatch: {} not found in {}".format(
                kwargs["number"], res.numbers
            )

        # Enough facilities
        if res.status != res.STATUS_RELEASED and res.raw_facility_name:
            assert (
                res.facilities.count() >= 1
            ), "No facility found: {}, {}, {}, {}, {}".format(
                res.name,
                res.numbers.values(),
                res.status,
                res.raw_facility_name,
                res.facility_url,
            )

        # Logged facility name
        if res.raw_facility_name:
            assert (
                FacilityNameResult.objects.filter(
                    administrator__name=self.admin_name,
                    name=res.raw_facility_name,
                    facility_url=res.facility_url,
                ).count()
                == 1
            )


class TestCalifornia(TestState):
    admin_name = "California"
    mod_name = "CA"

    def test_search(self, facilities):
        self.check_search(last_name="johnson")
        self.check_search(number="H72354")


class TestFederal(TestState):
    admin_name = "Federal Bureau of Prisons"
    mod_name = "federal"

    def test_search(self, facilities):
        self.check_search(first_name="john", last_name="smith")
        self.check_search(number="11563-027")


class TestFlorida(TestState):
    admin_name = "Florida"
    mod_name = "FL"

    def test_search(self, facilities):
        self.check_search(first_name="john", last_name="lee")
        self.check_search(number="J48121")


class TestNewYork(TestState):
    admin_name = "New York"
    mod_name = "NY"

    def test_search(self, facilities):
        self.check_search(number="13A1038", first_name="", last_name="")
        self.check_search(last_name="mitch", first_name="", number="")
        self.check_search(first_name="john", last_name="smith", number="")


class TestPennsylvania(TestState):
    admin_name = "Pennsylvania"
    mod_name = "PA"

    def test_search(self, facilities):
        self.check_search(first_name="jake", last_name="ackley")
        self.check_search(number="CN1835")


class TestTexas(TestState):
    admin_name = "Texas"
    mod_name = "TX"

    def test_search(self, facilities):
        self.check_search(first_name="john", last_name="smith")
        self.check_search(number="01715697")
