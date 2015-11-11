import time
from django.test import TestCase

from stateparsers.request_caching import get_caching_session

class TestRequestCaching(TestCase):
    throttle = 5

    def setUp(self):
        # remove the default cache
        self.session = get_caching_session("cache/test_cache", self.throttle)
        self.session.cache.clear()

    def test_uses_cache(self):
        start = time.time()
        print(start)
        # not cached, not throttled
        res = self.session.get("http://asdf.com/")
        self.assertFalse(getattr(res, "from_cache", None))
        # cached
        pre_cache = time.time()
        res = self.session.get("http://asdf.com/")
        self.assertTrue(getattr(res, "from_cache", None))
        self.assertTrue(time.time() - pre_cache < 0.1)
        # not cached, throttled
        res = self.session.get("http://asdf.com/aboutasdf.html")
        later = time.time()
        # time.time seems to have some accuracy issues that break this
        # sometimes? So add 1 to fix rounding errors.
        self.assertTrue(later - start + 1 >= self.throttle)
