import time
import pytest

from stateparsers.request_caching import get_caching_session

@pytest.fixture
def throttle():
    return 5

@pytest.fixture
def caching_session(throttle):
    session = get_caching_session("cache/test_cache", throttle)
    session.cache.clear()
    return session

@pytest.mark.django_db
def test_uses_cache(caching_session, throttle):
    start = time.time()

    # not cached, not throttled
    res = caching_session.get("http://asdf.com/")
    assert res.from_cache == False

    # cached
    pre_cache = time.time()
    res = caching_session.get("http://asdf.com/")
    assert res.from_cache == True
    assert time.time() - pre_cache < 0.1
    # not cached, throttled
    res = caching_session.get("http://asdf.com/aboutasdf.html")
    later = time.time()
    # time.time seems to have some accuracy issues that break this
    # sometimes? So add 1 to fix rounding errors.
    assert later - start + 1 >= throttle
