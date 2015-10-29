import time
import requests
import requests_cache
from django.test import TestCase

from stateparsers.request_caching import setup_cache

class TestRequestCaching(TestCase):
    throttle = 1

    def setUp(self):
        # remove the default cache
        requests_cache.uninstall_cache()
        # add a test-specific cache
        setup_cache("cache/test_cache", self.throttle);
        # clear the test specific cache
        requests_cache.clear();

    def test_uses_cache(self):
        start = time.time()
        res = requests.get("http://asdf.com/")
        self.assertFalse(getattr(res, "from_cache", None))
        res = requests.get("http://asdf.com/")
        self.assertTrue(getattr(res, "from_cache", None))
        res = requests.get("http://asdf.com/aboutasdf.html")
        later = time.time()
        self.assertTrue(later - start > self.throttle)
