from django.test import TestCase
import requests_cache
from stateparsers.request_caching import setup_cache

from stateparsers import search

class TestCalifornia(TestCase):
    fixtures = ['facilities.json']
    def setUp(self):
        requests_cache.uninstall_cache()
        setup_cache("cache/test_states")

    def test_name_search(self):
        results = search("california", last_name="johnson")
        self.assertTrue(len(results['results']) > 0)
        self.assertEquals(results['errors'], [])
        for res in results['results']:
            self.assertTrue(res.name.startswith("JOHNSON, "))
            self.assertEquals(res.facilities.count(), 1, "Bad facilities for {}, {}".format(res.extra['current_location'], res.extra['current_location_url']))


